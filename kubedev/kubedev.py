# coding=utf-8

import functools
import json
import operator
import pathlib
import subprocess
import sys
import time
import traceback
from io import StringIO
from os import environ, getenv, path
from uuid import uuid4

import colorama
import pkg_resources
import requests
import yaml

from kubedev.utils import KubedevConfig, KubernetesTools, YamlMerger

colorama.init(autoreset=True)

class RealSleep:
  def sleep(self, seconds: float):
    return time.sleep(seconds)

class RealDownloader:
  def download_file_to(self, url: str, headers: dict, target_filename: str, file_accessor) -> bool:
    response = requests.get(url, headers=headers)
    if response.ok:
      file_accessor.save_file(target_filename, response.text, True)
      return True
    else:
      return False

class RealFileAccessor:
  def load_file(self, filename):
    try:
      with open(filename, 'r') as f:
        return f.read()
    except FileNotFoundError:
      return None

  def save_file(self, filename, content, overwrite):
    if not overwrite and path.exists(filename):
      return
    targetDir = path.dirname(path.realpath(filename))
    pathlib.Path(targetDir).mkdir(parents=True, exist_ok=True)
    with open(filename, 'w') as f:
      f.write(content)

  def abspath(self, filepath):
    return path.abspath(filepath)

  def mkdirhier(self, path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)

class RealShellExecutor:
  def execute(self, commandWithArgs: list, envVars: dict = dict(), piped_input: str = None, check=True) -> int:
    """
    Execute a shell command.

    :param commandWithArgs: the commands to execute. Entries with the value None are ignored
    :param envVars: environment variables to set up for the command to execute
    :param piped_input: input to be piped into the command to execute
    """
    cmds = [cmd for cmd in commandWithArgs if cmd is not None]
    print(
      f'{colorama.Fore.CYAN}➡️   Executing "{" ".join(cmds)}"' +
      (f' (additional env vars: {" ".join(envVars.keys())})' if len(envVars) > 0 else ''),
      file=sys.stderr)
    return subprocess.run(cmds,
                          env      = {**environ, **envVars},
                          input    = piped_input if piped_input else None,
                          encoding = "UTF-8"     if piped_input else None,
                          check    = check
                          ).returncode

  def get_output(self, commandWithArgs, envVars: dict = dict(), check=True):
    cmds = [cmd for cmd in commandWithArgs if cmd is not None]
    print(f'{colorama.Fore.CYAN}➡️   Executing "{" ".join(cmds)}"')
    cmdResult = subprocess.run(cmds, check=check, env={**environ, **envVars}, stdout=subprocess.PIPE, encoding='utf-8')
    if cmdResult.returncode == 0:
      return cmdResult.stdout
    else:
      return None

  def is_tty(self):
    return sys.stdout.isatty()


class RealEnvAccessor:
  def getenv(self, name, default=None):
    return getenv(name, default)

  def environ(self):
    return environ


class RealTemplateAccessor:
  def load_template(self, file):
    return pkg_resources.resource_string(__name__, path.join('templates', file))


class RealPrinter:
  def print(self, message, isError):
    if isError:
      print(message, file=sys.stderr)
    else:
      print(message, file=sys.stdout)

class TagGenerator:
  def tag(self):
    s = str(uuid4())
    return s[0:s.find('-')]

def _load_template(file, variables, template_accessor):
  content = template_accessor.load_template(file)
  return _replace_variables(content.decode('utf-8'), variables)


def _replace_variables(text, variables):
  for key, value in variables.items():
    text = text.replace(f'%%{key}%%', f'{value}')
  return text


def _current_kubedev_docker_image():
  # TODO: Find out kubedev's own version number and put it here
  return 'kubedev/kubedev:1.0.0'


class Kubedev:

  def _load_config(self, configFileName, file_accessor=RealFileAccessor()):
    return json.loads(file_accessor.load_file(configFileName))
    # with open(configFileName) as f:
    #   return json.loads(f.read())

  def generate(self, configFileName, overwrite=False, file_accessor=RealFileAccessor(), env_accessor=RealEnvAccessor(), template_accessor=RealTemplateAccessor()):
    """
    Loads kubedev.json from the local directory and generates files according to kubedev.json's content.

    :param overwrite: Boolean flag whether to overwrite existing files (True), or keep files untouched (False, default).
    :param file_accessor: An injectable class instance that must implement load_file(self, filename) and save_file(self, filename, content).
                          Used to mock this function for unit tests.
    """
    return self.generate_from_config(self._load_config(configFileName), overwrite, file_accessor, env_accessor, template_accessor)

  def generate_from_config(self, kubedev, overwrite, file_accessor, env_accessor, template_accessor):
    """
    Generates files according to the config from the kubedev object, which must be a dict of the structure of a kubedev.json file.

    :param kubedev: A dict that contains the content of a `kubedev.json` file.
    :param overwrite: Boolean flag whether to overwrite existing files (True), or keep files untouched (False, default).
    :param file_accessor: An injectable class instance that must implement load_file(self, filename) and save_file(self, filename, content).
                          Used to mock this function for unit tests.
    """
    projectName = kubedev['name']
    imageRegistry = kubedev['imageRegistry']

    variables = KubedevConfig.get_global_variables(kubedev)

    envs = KubedevConfig.load_envs(kubedev, build=False, container=True)

    chartYamlTemplatePath = path.join('helm-chart', 'Chart.yaml')
    file_accessor.save_file(path.join(
        'helm-chart', 'Chart.yaml'), _load_template(chartYamlTemplatePath, variables, template_accessor), overwrite)

    portForwards = dict()  # Collect all port-forwards for deployments for tilt

    print('⚓ Generating helm-chart...')
    if 'deployments' in kubedev:
      (_, deploymentPortForwards) = self.generate_deployments(
          kubedev, projectName, envs, variables, imageRegistry, file_accessor, template_accessor, overwrite)
      portForwards.update(deploymentPortForwards)

    if 'cronjobs' in kubedev:
      self.generate_cronjobs(kubedev, projectName, envs, variables, imageRegistry, file_accessor, template_accessor, overwrite)

    images = KubedevConfig.get_images(kubedev, env_accessor)
    self.generate_ci(images, kubedev, projectName, envs, variables,
                     imageRegistry, file_accessor, overwrite)

    self.generate_tiltfile(
        projectName, images, portForwards, file_accessor, overwrite)

    self.generate_projects(images, file_accessor, template_accessor)

    return True

  def generate_cronjobs(self, kubedev, projectName, globalEnvs, variables, imageRegistry, file_accessor, template_accessor, overwrite):
    for cronjobName, value in kubedev['cronjobs'].items():
      name = KubedevConfig.collapse_names(projectName, cronjobName)
      envs = KubedevConfig.load_envs(value, build=False, container=True)
      additionalVars = {
          'KUBEDEV_CRONJOB_NAME': name,
          **variables
      }
      templatePath = path.join('helm-chart', 'cronjob.yaml')
      cronjob = yaml.safe_load(
          _load_template(templatePath, additionalVars, template_accessor))
      allEnvs = {**envs, **globalEnvs}
      image = f'{imageRegistry}/{name}'
      containers = [{
          'name': name,
          'image': image + ':{{.Values.KUBEDEV_TAG}}',
          'imagePullPolicy': 'Always',
          'env': [
              {
                  'name': envName,
                  'value': f'{{{{.Values.{envName}}}}}'
              } for (envName, envDef) in allEnvs.items()],
          # Security Best Practices:
          'securityContext': {
            'allowPrivilegeEscalation': False,
            'readOnlyRootFilesystem': True,
            'capabilities': {
              'drop': ['all']
            }
          }
      }]
      cronjob['spec']['jobTemplate']['spec']['template']['spec']['containers'] = containers
      deploymentYamlPath = path.join(
          'helm-chart', 'templates', 'cronjobs', cronjobName + '.yaml')
      file_accessor.save_file(
          deploymentYamlPath, yaml.safe_dump(cronjob), overwrite)

  def generate_deployments(self, kubedev, projectName, envs, variables, imageRegistry, file_accessor, template_accessor, overwrite):
    images = dict()  # Collect all images from deployments
    portForwards = dict()  # Collect all port-forwads for tilt
    for deploymentName, value in kubedev['deployments'].items():
      finalDeploymentName = KubedevConfig.collapse_names(
          projectName, deploymentName)
      ports = value['ports'] if 'ports' in value else dict()
      servicePorts = [
          port for (portName, port) in ports.items() if 'service' in port and 'container' in port]
      print(f'    🔱 Writing deployment {finalDeploymentName}' +
            ' (with service)' if len(servicePorts) > 0 else '')
      deployEnvs = KubedevConfig.load_envs(value, build=False, container=True)
      portForwards[deploymentName] = [
          {'dev': port['dev'], 'service': port['service']}
          for portName, port in ports.items()
          if 'dev' in port and 'service' in port
      ]
      replicas = int(value['replicas']) if 'replicas' in value else 2
      deployVars = {
          'KUBEDEV_DEPLOYMENT_NAME': finalDeploymentName,
          'KUBEDEV_DEPLOYMENT_REPLICAS': replicas,
          **variables
      }
      deploymentTemplatePath = path.join('helm-chart', 'deployment.yaml')
      deployment = yaml.safe_load(
          _load_template(deploymentTemplatePath, deployVars, template_accessor))
      allEnvs = {**envs, **deployEnvs}
      image = f'{imageRegistry}/{finalDeploymentName}'
      images[deploymentName] = {
          'image': image,
          'source': 'deployment'
      }
      containers = [{
          'name': finalDeploymentName,
          'image': image + ':{{.Values.KUBEDEV_TAG}}',
          'imagePullPolicy': 'Always',
          'env': [
              {
                  'name': envName,
                  'value': f'{{{{.Values.{envName}}}}}'
              } for (envName, envDef) in allEnvs.items()],
          'ports': [
              {
                  'name': portName,
                  'containerPort': int(value['container'])
              }
              for (portName, value) in ports.items() if 'container' in value
          ],
          # Security Best Practices:
          'securityContext': {
            'allowPrivilegeEscalation': False,
            'readOnlyRootFilesystem': True,
            'capabilities': {
              'drop': ['all']
            }
          }
      }]
      deployment['spec']['template']['spec']['containers'] = containers
      deploymentYamlPath = path.join(
          'helm-chart', 'templates', 'deployments', deploymentName + '.yaml')
      file_accessor.save_file(
          deploymentYamlPath, yaml.safe_dump(deployment), overwrite)
      servicePorts = [
          port for (portName, port) in ports.items() if 'service' in port and 'container' in port]
      if len(servicePorts) > 0:
        finalServiceName = finalDeploymentName
        serviceVars = {
            'KUBEDEV_SERVICE_NAME': finalServiceName,
            'KUBEDEV_SERVICE_TYPE': 'ClusterIP',
            **deployVars
        }
        serviceYamlPath = path.join(
            'helm-chart', 'templates', 'deployments', deploymentName + '_service.yaml')
        serviceTemplatePath = path.join('helm-chart', 'service.yaml')
        serviceYamlFile = file_accessor.load_file(serviceYamlPath)
        service = YamlMerger.merge(
            serviceYamlFile if not isinstance(
                serviceYamlFile, type(None)) else "",
            _load_template(serviceTemplatePath, serviceVars, template_accessor))
        service['spec']['ports'] = [
            {
                'name': portName,
                'port': int(port['service']),
                'targetPort': int(port['container'])
            } for (portName, port) in ports.items() if 'service' in port and 'container' in port
        ]
        file_accessor.save_file(
            serviceYamlPath, YamlMerger.dump(service), True)
    return (images, portForwards)

  def generate_ci(self, images, kubedev, projectName, envs, variables, imageRegistry, file_accessor, overwrite):
    print('🖥 Generating .gitlab-ci.yml...')
    oldCi = dict()
    try:
      with open('.gitlab-ci.yml', 'r') as f:
        # Load existing .gitlab-ci.yml, and merge contents
        oldCi = yaml.safe_load(f.read())
    except:
      pass  # Don't load .gitlab-ci.yml if it does not exists or fails otherwise

    if not 'stages' in oldCi:
      oldCi['stages'] = ['build-push', 'deploy']
    else:
      if not 'build-push' in oldCi['stages']:
        oldCi['stages'].append('build-push')
      if not 'deploy' in oldCi['stages']:
        oldCi['stages'].append('deploy')

    for imageKey in images.keys():
      jobName = f'build-push-{imageKey}'
      if not jobName in oldCi:
        oldCi[jobName] = {
            'stage': 'build-push',
            'image': _current_kubedev_docker_image(),
            'script': [
                'kubedev check',
                f'kubedev build {imageKey}',
                f'kubedev push {imageKey}'
            ],
            'variables': {
                'KUBEDEV_TAG': '${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}'
            }
        }

    if not 'deploy' in oldCi:
      oldCi['deploy'] = {
          'stage': 'deploy',
          'image': _current_kubedev_docker_image(),
          'script': [
              'kubedev check',
              'kubedev deploy --version ${CI_PIPELINE_IID}'
          ],
          'variables': {
              'KUBEDEV_TAG': '${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}'
          }
      }
    file_accessor.save_file('.gitlab-ci.yml', yaml.safe_dump(oldCi), overwrite)

  def generate_tiltfile(self, projectName, images, portForwards, file_accessor, overwrite):
    print('💫 Generating Tiltfile...')
    tiltfile = StringIO()
    for _, image in images.items():
      tiltfile.write(f"docker_build('{image['imageNameTagless']}', '{image['buildPath']}')\n")
    tiltfile.write('\n')

    tiltfile.write("k8s_yaml(local('kubedev template'))\n")
    tiltfile.write('\n')

    for portKey, portForward in portForwards.items():
      portForwardStr = ",".join(
          [f"'{p['dev']}:{p['service']}'" for p in portForward])
      tiltfile.write(
          f"k8s_resource('{KubedevConfig.collapse_names(projectName, portKey)}', port_forwards=[{portForwardStr}])\n")

    file_accessor.save_file('Tiltfile', tiltfile.getvalue(), overwrite)

  def generate_projects(self, images, file_accessor, template_accessor):
    for _, imageInfos in images.items():
      path = imageInfos["buildPath"]
      file_accessor.mkdirhier(path)
      templateFiles = {"Dockerfile": "Dockerfile"}
      if "usedFrameworks" in imageInfos:
        if "pipenv" in imageInfos["usedFrameworks"]:
          templateFiles = {
            "Dockerfile": "Dockerfile_pipenv",
            "app.py": "app.py",
            "Pipfile": "Pipfile",
            "Pipfile.lock": "Pipfile.lock",
          }
      for targetFile, templateFile in templateFiles.items():
        targetFilePath = f'{path}{targetFile}'
        print(f'💾 Generating {targetFilePath}...')
        file_accessor.save_file(targetFilePath, template_accessor.load_template(templateFile).decode('utf-8'), False)

  def _get_kubecontext_arg(self, env_accessor):
    e = env_accessor.getenv('KUBEDEV_KUBECONTEXT')
    return f'--kube-context {e}' if e != None and isinstance(e, str) and e != '' else ' '

  def _template(self, kubedev, shell_executor, env_accessor, file_accessor, get_output=False):
    variables = KubedevConfig.get_global_variables(kubedev)
    tag = KubedevConfig.get_tag(env_accessor)
    envs = KubedevConfig.get_helm_set_env_args(kubedev, env_accessor)
    command = [
        '/bin/sh',
        '-c',
        f'helm template ./helm-chart/ ' +
        f'--set KUBEDEV_TAG="{tag}"' +
        envs['cmdline']
    ]
    if not get_output:
      return shell_executor.execute(command, {**variables, **envs['envs']})
    else:
      return shell_executor.get_output(command, {**variables, **envs['envs']})

  def _deploy(
      self,
      kubedev: dict,
      kubeconfig: str,
      tag: str,
      release_name: str,
      docker_network: str,
      shell_executor: object,
      env_accessor: object,
      file_accessor: object,
      get_output: bool = False):
    variables = KubedevConfig.get_global_variables(kubedev)
    if docker_network is not None:
      kubeContext = env_accessor.getenv('KUBEDEV_KUBECONTEXT')
      envs = KubedevConfig.get_helm_set_env_args(kubedev, env_accessor, cmdline_as_list=True)
      command = [
          'docker',
          'run',
          '-i',
          '--rm',
          '--network',
          docker_network,
          '--volume',
          f'{KubedevConfig.wsl_normalize(kubeconfig, file_accessor, shell_executor)}:/tmp/kube_config',
          '--volume',
          f'{KubedevConfig.wsl_normalize("helm-chart/", file_accessor, shell_executor)}:/app/helm-chart/',
          'alpine/helm:2.16.9',
          'upgrade',
          release_name,
          '/app/helm-chart/',
          '--install',
          '--wait',
          '--kubeconfig',
          '/tmp/kube_config'] + \
          (["--kube-context", kubeContext] if kubeContext != None else []) + \
          ['--set', f'KUBEDEV_TAG={tag}'] + \
          envs['cmdline']
    else:
      envs = KubedevConfig.get_helm_set_env_args(kubedev, env_accessor, cmdline_as_list = False)
      command = [
          '/bin/sh',
          '-c',
          f'helm upgrade {release_name} ./helm-chart/ --install --wait ' +
          f'--kubeconfig {kubeconfig} {self._get_kubecontext_arg(env_accessor)} ' +
          f'--set KUBEDEV_TAG="{tag}"' +
          envs['cmdline']
      ]
    if not get_output:
      return shell_executor.execute(command, {**variables, **envs['envs']})
    else:
      return shell_executor.get_output(command, {**variables, **envs['envs']})

  def template(self, configFileName, shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor(), file_accessor=RealFileAccessor()):
    return self.template_from_config(
        self._load_config(configFileName), shell_executor, env_accessor, file_accessor)

  def template_from_config(self,
                           kubedev,
                           shell_executor,
                           env_accessor=RealEnvAccessor(),
                           file_accessor=RealFileAccessor(),
                           get_output=False):
    return self._template(kubedev,
                                    shell_executor,
                                    env_accessor,
                                    file_accessor,
                                    get_output)

  def deploy(self, configFileName, shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor(), file_accessor=RealFileAccessor()):
    return self.deploy_from_config(
        self._load_config(configFileName), shell_executor, env_accessor, file_accessor)

  def deploy_from_config(self, kubedev, shell_executor, env_accessor, file_accessor):
    release_name = KubedevConfig.get_helm_release_name(kubedev)
    kubeconfig = KubedevConfig.get_kubeconfig_path(env_accessor, file_accessor)
    tag = KubedevConfig.get_tag(env_accessor)
    return self._deploy(kubedev, kubeconfig, tag, release_name, None, shell_executor, env_accessor, file_accessor)

  def _create_docker_config(self, file_accessor, env_accessor):
    envCi = env_accessor.getenv('CI')
    envDockerAuthConfig = env_accessor.getenv('DOCKER_AUTH_CONFIG')
    envHome = env_accessor.getenv('HOME')
    if envCi is not None and envDockerAuthConfig is not None and envHome is not None:
      dockerConfigPath = path.join(envHome, '.docker/config.json')
      if file_accessor.load_file(dockerConfigPath) is None:
        print(f'{colorama.Fore.YELLOW}CI environment detected and no docker config found.')
        print(f'{colorama.Fore.YELLOW}Storing content of ${{DOCKER_AUTH_CONFIG}} to file {dockerConfigPath}.')
        file_accessor.save_file(dockerConfigPath, envDockerAuthConfig, overwrite=False)
        return True
    return False

  def build_from_image(self, image: dict, force_tag: str, env_accessor: object, shell_executor: object) -> int:
    if force_tag is None:
      imageTag = image['imageName']
    else:
      imageTag = f"{image['imageNameTagless']}:{force_tag}"
    (argsCmdLine, extraEnv) = KubedevConfig.get_docker_build_args(image, env_accessor=env_accessor)
    call = [
        '/bin/sh',
        '-c',
        f"docker build -t {imageTag} " +
        argsCmdLine +
        f"{image['buildPath']}"
    ]
    return shell_executor.execute(call, envVars=extraEnv, check=False)

  def build(self, configFileName, container, file_accessor=RealFileAccessor(), shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor()):
    return self.build_from_config(
        self._load_config(configFileName), container=container, force_tag=None, file_accessor=file_accessor, shell_executor=shell_executor, env_accessor=env_accessor)

  def build_from_config(self, kubedev, container, force_tag, file_accessor, shell_executor, env_accessor):
    if file_accessor is not None:
      self._create_docker_config(file_accessor, env_accessor)
    images = KubedevConfig.get_images(kubedev, env_accessor)
    if not container in images:
      raise KeyError(
          f"Container {container} is not defined in kubedev config.")
    else:
      image = images[container]
      return self.build_from_image(image, force_tag, env_accessor, shell_executor)

  def _push_image(self, image: str, shell_executor: object) -> int:
      call = [
          '/bin/sh',
          '-c',
          f"docker push {image}"
      ]
      return shell_executor.execute(call, dict())

  def push(self, configFileName, container, file_accessor=RealFileAccessor(), shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor()):
    return self.push_from_config(
        self._load_config(configFileName), container=container, file_accessor=file_accessor, shell_executor=shell_executor, env_accessor=env_accessor)

  def push_from_config(self, kubedev, container, file_accessor, shell_executor, env_accessor):
    self._create_docker_config(file_accessor, env_accessor)
    images = KubedevConfig.get_images(kubedev, env_accessor)
    if not container in images:
      raise KeyError(
          f"Container {container} is not defined in kubedev config.")
    else:
      image = images[container]
      return self._push_image(image['imageName'], shell_executor)

  def _load_polaris_config(self, kubedev, downloader, file_accessor, env_accessor) -> str:
    if not "securityChecks" in kubedev:
      return None
    securityChecks = kubedev["securityChecks"]

    if not "polaris" in securityChecks:
      return None

    polarisConfigObject = securityChecks["polaris"]
    if not "configFile" in polarisConfigObject:
      return None
    polarisConfigFile = KubedevConfig.expand_variables(polarisConfigObject["configFile"], env_accessor)

    if "configDownload" in polarisConfigObject:
      polarisDownloadObject = polarisConfigObject["configDownload"]

      if "url" in polarisDownloadObject:
        polarisConfigUrl = KubedevConfig.expand_variables(polarisDownloadObject["url"], env_accessor)
        headersRaw = polarisDownloadObject["headers"] if "headers" in polarisDownloadObject else dict()
        headers = {KubedevConfig.expand_variables(key, env_accessor):KubedevConfig.expand_variables(value, env_accessor) for key, value in headersRaw.items()}
        if len(headers) == 0:
          print(f'INFO: Downloading {polarisDownloadObject["url"]} to local file {polarisConfigFile}.')
        else:
          print(f'INFO: Downloading {polarisDownloadObject["url"]} to local file {polarisConfigFile} with headers {list(headers.keys())}.')
        if not downloader.download_file_to(polarisConfigUrl, headers, polarisConfigFile, file_accessor):
          print(f"WARNING: Failed to download polaris config from {polarisDownloadObject['url']}, not using a custom polaris config..", file=sys.stderr)
          return None

    if file_accessor.load_file(polarisConfigFile) == None:
        print(f"WARNING: Polaris config file {polarisConfigFile} does not exist, not using custom polaris config.", file=sys.stderr)
        return None

    return polarisConfigFile

  def audit(self, configFileName):
    """
    Check a helm-chart for compliance.

    :param configFileName: kubedev configuration filename
    """
    return self.audit_from_config(self._load_config(configFileName),
                        downloader=RealDownloader(),
                        file_accessor=RealFileAccessor(),
                        shell=RealShellExecutor(),
                        env_accessor=RealEnvAccessor())

  def audit_from_config(self,
                        kubedev,
                        downloader,
                        file_accessor,
                        shell,
                        env_accessor):
    polarisConfigFile = self._load_polaris_config(kubedev, downloader, file_accessor, env_accessor)

    k8s_spec        = self.template_from_config(
                        kubedev=kubedev,
                        shell_executor=shell,
                        env_accessor=env_accessor,
                        get_output=True)
    polaris_audit   = [ "polaris",
                        "audit",
                        "--config" if polarisConfigFile != None else None,
                        polarisConfigFile if polarisConfigFile != None else None,
                        "--set-exit-code-on-danger",
                        "--format",
                        "yaml",
                        "--audit-path",
                        "-"]
    audit_exit_code = shell.execute(
                          commandWithArgs = polaris_audit,
                          piped_input     = k8s_spec)
    return audit_exit_code

  def check(self, configFileName, commands, env_accessor=RealEnvAccessor(), printer=RealPrinter(), file_accessor=RealFileAccessor()):
    return self.check_from_config(
      kubedev       = self._load_config(configFileName, file_accessor),
      commands      = commands,
      env_accessor  = env_accessor,
      printer       = printer,
      file_accessor = file_accessor)

  def check_from_config(self, kubedev, commands, env_accessor, printer, file_accessor):
    def is_command(cmd):
      return len(commands) == 0 or cmd in commands

    result = True

    # check if all environment variables are set
    if is_command('generate'):
      if not 'name' in kubedev:
        printer.print(
            '❌ Required field "name" is missing in kubedev.json', True)
        result = False

      if not 'imageRegistry' in kubedev:
        printer.print(
            '❌ Required field "imageRegistry" is missing in kubedev.json', True)
        result = False

      if not 'imagePullSecrets' in kubedev:
        printer.print(
            '❌ Required field "imagePullSecrets" is missing in kubedev.json', True)
        result = False

    envs = KubedevConfig.get_all_envs(kubedev, build=is_command(
        'build'), container=is_command('deploy') or is_command('template')).keys()
    for env in sorted(envs):
      if isinstance(env_accessor.getenv(env), type(None)):
        printer.print(
            f'❌ Required environment variable "{env}" is not defined', True)
        result = False

    if result:
      print('🎉🥳  Yay, all environment variables are set and kubedev.json is well-formed! 🥳🎉')
      print('🎉🥳                              !!! DEV ON !!!                              🥳🎉')
    else:
      print('❌ Check failed')
    return result

  def run(self, configFileName, container, env_accessor=RealEnvAccessor(), shell_executor=RealShellExecutor(), printer=RealPrinter(), file_accessor=RealFileAccessor()):
    return self.run_from_config(
        self._load_config(configFileName, file_accessor), container, env_accessor=env_accessor, printer=printer, file_accessor=file_accessor)

  def run_from_config(self,
                      kubedev,
                      container,
                      env_accessor=RealEnvAccessor(),
                      shell_executor=RealShellExecutor(),
                      printer=RealPrinter(),
                      file_accessor=RealFileAccessor(),
                      tag_generator=TagGenerator()):
    images = KubedevConfig.get_images(kubedev, env_accessor)
    if not container in images:
      raise KeyError(
          f"Container {container} is not defined in kubedev config.")
    else:
      image = images[container]
      currentTag = tag_generator.tag()
      buildResult = self.build_from_config(
          kubedev, container, currentTag, file_accessor=None, shell_executor=shell_executor, env_accessor=env_accessor)
      interactive_flags = "--tty " if shell_executor.is_tty() else ""

      if buildResult != 0:
        return buildResult
      else:
        (runEnvArgs, extraEnvs) = KubedevConfig.get_docker_run_envs(image, env_accessor=env_accessor)

        command = [
          '/bin/sh',
          '-c',
          f"docker run --interactive {interactive_flags}--rm " +
          KubedevConfig.get_docker_run_volumes(image, file_accessor, shell_executor) +
          KubedevConfig.get_docker_run_ports(image) +
          runEnvArgs +
          f"{image['imageNameTagless']}:{currentTag}"
        ]
        return shell_executor.execute(command, envVars=extraEnvs, check=False)

  @staticmethod
  def _build_cluster_config_mounts(clusterConfig: str, file_accessor: object, shell_executor: object) -> list:
    if clusterConfig != None:
      return ["--volume", f"{KubedevConfig.wsl_normalize(clusterConfig, file_accessor, shell_executor)}:/tmp/kube_config", "--env", "KUBECONFIG=/tmp/kube_config"]
    else:
      return []

  def _run_docker_detached(
    self,
    network: str,
    name: str,
    ports: list,
    rawImage: str,
    images: dict,
    variables: dict,
    env_accessor: object,
    shell_executor: object,
    file_accessor: object) -> (str, bool):
      """
      Starts a container in detached mode and returns it's ID.

      Returns None when the start failed.
      """
      (imageDef, image, requiredEnvs, isFromKubedev) = Kubedev._build_image(rawImage, images)
      filteredRequiredEnvs = sorted([env for env in requiredEnvs if not env in variables]) # Note: the sorted() is important, otherwise the order would be
      if isFromKubedev and env_accessor.getenv('CI') is None:
        self.build_from_image(imageDef, "none", env_accessor, shell_executor)
      requiredEnvForwards = functools.reduce(operator.concat, [["--env", f'{envName}="${{{envName}}}"'] for envName in filteredRequiredEnvs], []) if isFromKubedev else []
      return self._run_docker_detached_impl(
        network,
        name,
        image,
        KubedevConfig.get_docker_run_volumes_list(imageDef, file_accessor, shell_executor) + \
        requiredEnvForwards + \
        functools.reduce(operator.concat, [["--env", f'{varName}="{varValue}"'] for varName, varValue in variables.items()], []) + \
        functools.reduce(operator.concat, [["--publish", str(port)] for port in ports], []),
        dict(),
        shell_executor)


  def _run_docker_detached_impl(self, network: str, name: str, image: str, additionalArgs: list, shellEnvs: dict, shell_executor: object):
      print(f'Running detached: {name} (image: {image})')
      cmdRm = ["docker", "rm", "--force", name]
      shell_executor.execute(cmdRm, check=False) # To be sure, first try to delete the container that we want to create

      cmdCreate = [
        "/bin/sh",
        "-c",
        " ".join([
          "docker",
          "create",
          "--network", network,
          "--name", name,
          "--rm"] + \
          additionalArgs + \
          [image])]
      dockerIdRaw = shell_executor.get_output(cmdCreate, envVars=shellEnvs, check=False)
      print(f"> {dockerIdRaw}")
      if dockerIdRaw is None or dockerIdRaw == "":
          return (dockerIdRaw, name, False)
      else:
          dockerId = dockerIdRaw.strip(" \r\n\t")
          cmdStart = ["docker", "start", dockerId]
          if shell_executor.execute(cmdStart, check=False) == 0:
              return (dockerId, name, True)
          else:
              return (dockerId, name, False)

  @staticmethod
  def _build_image(name: str, images: dict) -> (str, bool):
      if len(name) > 3 and name[0] == '{' and name[-1] == '}':
          appName = name[1:-1]
          if appName in images:
              return (images[appName], images[appName]['imageName'], images[appName]['containerEnvs'].keys(), True)
          else:
              raise Exception(f'App "{appName}" is referenced by the system test service {name}, but is not defined in kubedev config')
      return (dict(), name, dict(), False)

  @staticmethod
  def _field_required(obj: dict, field: str, objectName: str):
      if not field in obj:
          raise Exception(f'The field {field} is required in {objectName}')
      else:
          return obj[field]

  @staticmethod
  def _field_optional(obj: dict, field: str, default):
      if not field in obj:
          return default
      else:
          return obj[field]

  @staticmethod
  def _rewrite_kubeconfig_to(file: str, host: str, port: int, file_accessor: object):
    kubeConfFile = file_accessor.load_file(file)
    if kubeConfFile != None:
      kubeConf = yaml.safe_load(kubeConfFile)
      for cluster in kubeConf['clusters']:
        cluster['cluster']['server'] = f'https://{host}:{port}'
      kubeConfNew = yaml.safe_dump(kubeConf)
      file_accessor.save_file(file, kubeConfNew, overwrite=True)
      return kubeConfNew

  def system_test(self,
                  configFileName: str,
                  appName: str,
                  file_accessor=RealFileAccessor(),
                  env_accessor=RealEnvAccessor(),
                  shell_executor=RealShellExecutor(),
                  tag_generator=TagGenerator(),
                  sleeper=RealSleep()) -> bool:
    return self.system_test_from_config(
      self._load_config(configFileName, file_accessor),
      appName,
      file_accessor=file_accessor,
      env_accessor=env_accessor,
      shell_executor=shell_executor,
      tag_generator=tag_generator,
      sleeper=sleeper)

  def system_test_from_config(self, kubedev, appName: str, file_accessor, env_accessor, shell_executor, tag_generator, sleeper) -> bool:
      '''
      Runs the system tests for an app as defined in the kubedev config.

      @param requiredEnvs Are the required-envs from the global and the deployment level that this system test definition comes from
      @param images Is the list of all available images from apps defined in the kubedev config
      @param systemTestDefinition Is the node "systemTests" from this apps definition
      @param shell_executor Is used to execute shell commands
      '''

      self._create_docker_config(file_accessor, env_accessor)

      images = KubedevConfig.get_images(kubedev, env_accessor)
      apps = KubedevConfig.get_all_app_definitions(kubedev)
      if not appName in apps:
        print(f'{colorama.Fore.RED} Invalid app {appName} specified. Available apps: {apps.keys()}', file=sys.stderr)
        return False

      app = apps[appName]
      if not 'systemTest' in app:
        print(f'{colorama.Fore.RED} App {appName} does not define a systemTest.', file=sys.stderr)
        return False

      systemTestDefinition = app['systemTest']

      # Step #1: Build the system test container
      globalVariables = self._field_optional(systemTestDefinition, "variables", dict())

      testContainer = self._field_optional(systemTestDefinition, "testContainer", dict())
      buildArgs = self._field_optional(testContainer, "buildArgs", dict())
      variables = {**globalVariables, **self._field_optional(testContainer, "variables", dict())}
      requiredEnvs = images[appName]['containerEnvs']
      (filteredRequiredEnvs, additionalEnvs) = KubedevConfig.prepare_envs(requiredEnvs, env_accessor)

      containerDir = f"./systemTests/{appName}/"
      uuid = tag_generator.tag()
      tag = f"local-{appName}-system-tests-{uuid}"
      network = tag
      appType = app['type']
      cmdBuild = [
        "/bin/sh",
        "-c",
        " ".join([
          "docker",
          "build",
          "-t",
          tag
          ] + functools.reduce(operator.concat, [["--build-args", f'{arg}="{value}"'] for arg, value in buildArgs.items()], []) + [containerDir])]
      if shell_executor.execute(cmdBuild, envVars=buildArgs, check=False) != 0:
          return False
      # Step #1.1: For CronJobs: Build and push all apps
      if appType == 'cronjobs':
        for app in apps:
          self.build_from_config(kubedev, appName, uuid, file_accessor, shell_executor, env_accessor)
          self._push_image(f"{images[appName]['imageNameTagless']}:{uuid}", shell_executor)

      # Step #2: Create the docker network, or spin up a Kind cluster:
      if appType == 'cronjobs':
          file_accessor.mkdirhier('.kubedev')
          serviceName = kubedev['name']
          clusterName = f'kind-{serviceName}-{uuid}'
          clusterConfig = f'.kubedev/kind_config_{serviceName}-{uuid}'

          cmdKindCreateCluster = [
              'kind',
              'create',
              'cluster',
              '--kubeconfig',
              clusterConfig,
              '--wait',
              '10m',
              '--name',
              clusterName
          ]
          additionalVars = {
              'KIND_EXPERIMENTAL_DOCKER_NETWORK': network
          }
          # Spin up a new one-node Kubernetes-in-Docker cluster via `kind` (https://kind.sigs.k8s.io/)
          if shell_executor.execute(cmdKindCreateCluster, additionalVars) != 0:
            return False
          clusterConfigContent = Kubedev._rewrite_kubeconfig_to(clusterConfig, f"{clusterName}-control-plane", 6443, file_accessor=file_accessor)
      elif appType == 'deployments':
          clusterConfig = None
          cmdNetworkCreate = ["docker", "network", "create", network]
          if shell_executor.execute(cmdNetworkCreate, check=False) != 0:
              return False
      else:
          raise NotImplementedError(f"Can not run system tests for app type {appType}")

      result = False
      startedContainers = []
      try:
          # Step #3: Start the service containers
          startedContainers = [
              self._run_docker_detached(
                  network,
                  KubedevConfig.expand_variables(self._field_required(service, 'hostname', 'systemTest.service'), env_accessor, self._field_optional(service, 'variables', dict())),
                  self._field_required(service, 'ports', 'systemTest.service'),
                  serviceKey,
                  images,
                  {**globalVariables, **self._field_optional(service, 'variables', dict())},
                  env_accessor,
                  shell_executor,
                  file_accessor) for serviceKey, service in self._field_optional(systemTestDefinition, 'services', dict()).items()]
          if appType == 'cronjobs':
            runCronJobApiKey = tag_generator.tag()
            # Add variables for the test container to access the kubedev-run-cronjob-api service:
            variables = {
              **variables,
              "KUBEDEV_SYSTEMTEST_DAEMON_APIKEY": runCronJobApiKey,
              "KUBEDEV_SYSTEMTEST_DAEMON_ENDPOINT": f"http://kubedev-run-cronjob-api:5000/execute"
            }

            # Step #3.1: For CronJobs: Start the 'kubedev-run-cronjob-api' service
            startedContainers = startedContainers + [
              self._run_docker_detached_impl(
                network,
                'kubedev-run-cronjob-api',
                'danielkun/kubedev-systemtest-daemon:v0.01',
                [
                  "--env",
                  f'KUBEDEV_SYSTEMTEST_DAEMON_APIKEY="{runCronJobApiKey}"',
                  "--env",
                  f'KUBEDEV_SYSTEMTEST_DAEMON_CRONJOB="{images[appName]["appName"]}"',
                  "--env",
                  'KUBEDEV_SYSTEMTEST_DAEMON_KUBECONFIG="${KUBEDEV_SYSTEMTEST_DAEMON_KUBECONFIG}"'
                ],
                {
                  "KUBEDEV_SYSTEMTEST_DAEMON_KUBECONFIG": clusterConfigContent
                },
                shell_executor
              )
            ]
            # Step #3.2: For CronJobs: Init helm, set docker registry secret and deploy this helm-chart
            wslClusterConfig = KubedevConfig.wsl_normalize(clusterConfig, file_accessor, shell_executor)
            if not KubernetesTools.apply(tag, wslClusterConfig, KubernetesTools.get_tiller_rbac_setup(), shell_executor):
              return False

            if KubernetesTools.kubectl(
              tag,
              wslClusterConfig,
              {"DOCKER_AUTH_CONFIG"},
              ["create",
                "secret",
                "generic",
                kubedev['imagePullSecrets'],
                "--type",
                "kubernetes.io/dockerconfigjson",
                '--from-literal=.dockerconfigjson="${DOCKER_AUTH_CONFIG}"'],
              shell_executor) != 0:
              return False

            cmdHelmInit = [
              'docker',
              'run',
              '-i',
              '--rm',
              '--network',
              tag,
              '--volume',
              f'{wslClusterConfig}:/tmp/kube_config',
              'alpine/helm:2.16.9',
              '--kubeconfig',
              '/tmp/kube_config',
              'init',
              '--service-account',
              'tiller'
            ]
            if shell_executor.execute(cmdHelmInit, check=False) != 0:
                return False
            timeout = 600
            print(f'{colorama.Fore.YELLOW}Waiting {timeout} seconds for Tiller deployment to become ready...')
            if not KubernetesTools.wait_for_deployment(tag, wslClusterConfig, "kube-system", "tiller-deploy", timeout, shell_executor, sleeper):
              print(f'{colorama.Fore.RED}Tiller deployment did not become ready within timeout of {timeout} seconds :-(')
              return False
            if self._deploy(kubedev, clusterConfig, uuid, tag, tag, shell_executor, env_accessor, file_accessor) != 0:
              return False

          numSleepSeconds = 5
          print(f'{colorama.Fore.YELLOW}TODO: Sleeping for {numSleepSeconds} seconds instead of pinging the exposed ports')
          # Step #4: Wait for the services to become ready
          sleeper.sleep(numSleepSeconds)

          print(f'{colorama.Fore.GREEN}======================================')
          print(f'{colorama.Fore.GREEN}🚀🚀🚀 PREPARATION COMPLETED.')
          print(f'{colorama.Fore.GREEN}🚀🚀🚀 SYSTEM TESTS ARE STARTING NOW:')
          print(f'{colorama.Fore.GREEN}======================================')

          # Step #5: Run the system test container
          cmdRunSystemTests = [
              "/bin/sh",
              "-c",
              " ".join([
              "docker",
              "run",
              "--rm",
              "--network", network,
              "--name", f"{appName}-system-tests-{uuid}",
              "--interactive"] + \
              Kubedev._build_cluster_config_mounts(clusterConfig, file_accessor=file_accessor, shell_executor=shell_executor) + \
              functools.reduce(operator.concat, [["--env", f'{envName}="${{{attribs["targetName"]}}}"'] for envName, attribs in filteredRequiredEnvs.items()], []) + \
              functools.reduce(operator.concat, [["--env", f'{varName}="{varValue}"'] for varName, varValue in variables.items()], []) + \
              [tag])]
          if shell_executor.execute(cmdRunSystemTests, envVars=additionalEnvs, check=False) == 0:
              result = True
          else:
              print()
              print(f'{colorama.Fore.RED}^^^ See logs of the system test above.')
              print()
              result = False
          return result
      except:
          traceback.print_exc()
      finally:
          for startedContainer in startedContainers:
              containerId = startedContainer[0]
              if containerId != None and containerId != "":
                  if result == False:
                      cmdLogs = ["docker", "logs", containerId]
                      shell_executor.execute(cmdLogs, check=False)
                      print()
                      print(f'{colorama.Fore.RED}^^^ See logs of the service "{startedContainer[1]}" above')
                      print()
                  # Cleanup #2: Remove the service containers
                  cmdRm = ["docker", "rm", "--force", containerId]
                  shell_executor.execute(cmdRm, check=False)

          # Cleanup #2: Remove the docker network / Kind cluster
          if appType == 'cronjobs':
              cmdKindDeleteCluster = [
                  'kind',
                  'delete',
                  'cluster',
                  '--name',
                  clusterName
              ]
              shell_executor.execute(cmdKindDeleteCluster)
          cmdNetworkRm = ["docker", "network", "rm", tag]
          shell_executor.execute(cmdNetworkRm, check=False)

          if result:
              print()
              print(f'{colorama.Fore.GREEN}System tests succeeded! 🌟🎉🥳')
              print()
              return 0
          else:
              print()
              print(f'{colorama.Fore.RED}System tests failed! The logs of the services and the system test have been printed above.')
              print()
              return 1

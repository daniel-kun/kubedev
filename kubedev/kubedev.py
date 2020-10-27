# coding=utf-8

import json
import pathlib
import subprocess
import sys
from io import StringIO
from os import environ, getenv, path
from uuid import uuid4

import pkg_resources
import requests
import yaml

from kubedev.utils import KubedevConfig, YamlMerger


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

  def mkdirhier(self, path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


class RealShellExecutor:
  def execute(self, commandWithArgs: list, envVars: dict = dict(), piped_input: str = None):
    """
    Execute a shell command.

    :param commandWithArgs: the commands to execute. Entries with the value None are ignored
    :param envVars: environment variables to set up for the command to execute
    :param piped_input: input to be piped into the command to execute
    """
    cmds = [cmd for cmd in commandWithArgs if cmd is not None]
    print(
      f'➡️   Executing "{" ".join(cmds)}" '
      f'(additional env vars: {" ".join(envVars.keys())})',
      file=sys.stderr)
    return subprocess.run(cmds,
                          env      = {**environ, **envVars},
                          input    = piped_input if piped_input else None,
                          encoding = "UTF-8"     if piped_input else None,
                          ).returncode

  def get_output(self, commandWithArgs):
    cmds = [cmd for cmd in commandWithArgs if cmd is not None]
    cmdResult = subprocess.run(cmds, check=True, stdout=subprocess.PIPE, encoding='utf-8')
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
    return str(uuid4()).replace('-', '')

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

    portForwards = dict()  # Collect all port-forwards for deployments and daemonsets for tilt

    print('⚓ Generating helm-chart...')
    if 'deployments' in kubedev:
      (_, deploymentPortForwards) = self.generate_deployments(
          kubedev, projectName, envs, variables, imageRegistry, file_accessor, template_accessor, overwrite)
      portForwards.update(deploymentPortForwards)

    images = KubedevConfig.get_images(kubedev, env_accessor)
    self.generate_ci(images, kubedev, projectName, envs, variables,
                     imageRegistry, file_accessor, overwrite)

    self.generate_tiltfile(
        projectName, images, portForwards, file_accessor, overwrite)

    self.generate_projects(images, file_accessor, template_accessor)

    return True

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
    command = [
        '/bin/sh',
        '-c',
        f'helm template ./helm-chart/ ' +
        f'--set KUBEDEV_TAG="{tag}"' +
        KubedevConfig.get_helm_set_env_args(kubedev)
    ]
    if not get_output:
      return shell_executor.execute(command, variables)
    else:
      return shell_executor.get_output(command)

  def _deploy(self, kubedev, release_name, shell_executor, env_accessor, file_accessor, get_output=False):
    variables = KubedevConfig.get_global_variables(kubedev)
    tag = KubedevConfig.get_tag(env_accessor)
    kubeconfig = KubedevConfig.get_kubeconfig_path(env_accessor, file_accessor)
    command = [
        '/bin/sh',
        '-c',
        f'helm upgrade {release_name} ./helm-chart/ --install --wait ' +
        f'--kubeconfig {kubeconfig} {self._get_kubecontext_arg(env_accessor)} ' +
        f'--set KUBEDEV_TAG="{tag}"' +
        KubedevConfig.get_helm_set_env_args(kubedev)
    ]
    if not get_output:
      return shell_executor.execute(command, variables)
    else:
      return shell_executor.get_output(command)

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
    return self._deploy(kubedev, release_name, shell_executor, env_accessor, file_accessor)

  def _create_docker_config(self, file_accessor, env_accessor):
    envCi = env_accessor.getenv('CI')
    envDockerAuthConfig = env_accessor.getenv('DOCKER_AUTH_CONFIG')
    envHome = env_accessor.getenv('HOME')
    if envCi is not None and envDockerAuthConfig is not None and envHome is not None:
      dockerConfigPath = path.join(envHome, '.docker/config.json')
      if file_accessor.load_file(dockerConfigPath) is None:
        print('NOTICE NOTICE NOTICE')
        print('CI environment detected and no docker config found.')
        print(f'Storing content of ${{DOCKER_AUTH_CONFIG}} to file {dockerConfigPath}.')
        print('NOTICE NOTICE NOTICE')
        print()
        file_accessor.save_file(dockerConfigPath, envDockerAuthConfig, overwrite=False)
        return True
    return False


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
      if force_tag is None:
        imageTag = image['imageName']
      else:
        imageTag = f"{image['imageNameTagless']}:{force_tag}"
      call = [
          '/bin/sh',
          '-c',
          f"docker build -t {imageTag} " +
          KubedevConfig.get_docker_build_args(image) +
          f"{image['buildPath']}"
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
      call = [
          '/bin/sh',
          '-c',
          f"docker push {image['imageName']}"
      ]
      return shell_executor.execute(call, dict())

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

    envs = KubedevConfig.get_all_env_names(kubedev, build=is_command(
        'build'), container=is_command('deploy') or is_command('template'))
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
        command = [
          '/bin/sh',
          '-c',
          f"docker run --interactive {interactive_flags}--rm " +
          KubedevConfig.get_docker_run_volumes(image, file_accessor, shell_executor) +
          KubedevConfig.get_docker_run_ports(image) +
          KubedevConfig.get_docker_run_envs(image) +
          f"{image['imageNameTagless']}:{currentTag}"
        ]
        runResult = shell_executor.execute(command, dict())
        return runResult

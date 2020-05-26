import json
import pathlib
import subprocess
import sys
from io import StringIO
from os import environ, getenv, path

import pkg_resources
import yaml
from kubedev.utils import KubedevConfig, YamlMerger


class RealFileAccessor:
  def load_file(self, filename):
    try:
      with open(filename, 'r') as f:
        return f.read()
    except FileNotFoundError:
      return ''

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
  def execute(self, commandWithArgs, envVars):
    print(
        f'➡️   Executing "{" ".join(commandWithArgs)}" (additional env vars: {" ".join(envVars.keys())})', file=sys.stderr)
    return subprocess.run(commandWithArgs, env={**environ, **envVars})


class RealEnvAccessor:
  def getenv(self, name, default=None):
    return getenv(name, default)


class RealTemplateAccessor:
  def load_template(self, file):
    return pkg_resources.resource_string(__name__, path.join('templates', file))


class RealPrinter:
  def print(self, message, isError):
    if isError:
      print(message, file=sys.stderr)
    else:
      print(message, file=sys.stdout)


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

  def _load_config(self, configFileName):
    with open(configFileName) as f:
      return json.loads(f.read())

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

    images = dict()  # Collect all images across deployments, cronjobs, etc.
    portForwards = dict()  # Collect all port-forwards for deployments and daemonsets for tilt

    print('⚓ Generating helm-chart...')
    if 'deployments' in kubedev:
      (deploymentImages, deploymentPortForwards) = self.generate_deployments(
          kubedev, projectName, envs, variables, imageRegistry, file_accessor, template_accessor, overwrite)
      images.update(deploymentImages)
      portForwards.update(deploymentPortForwards)

    self.generate_ci(images, kubedev, projectName, envs, variables,
                     imageRegistry, file_accessor, overwrite)

    self.generate_tiltfile(
        projectName, images, portForwards, file_accessor, overwrite)

    self.generate_projects(images, file_accessor)

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
          ]
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
    for imageKey, image in images.items():
      tiltfile.write(f"docker_build('{image['image']}', '{imageKey}')\n")
    tiltfile.write('\n')

    tiltfile.write("k8s_yaml(local('kubedev template'))\n")
    tiltfile.write('\n')

    for portKey, portForward in portForwards.items():
      portForwardStr = ",".join(
          [f"'{p['dev']}:{p['service']}'" for p in portForward])
      tiltfile.write(
          f"k8s_resource('{projectName}-{portKey}', port_forwards=[{portForwardStr}])\n")

    file_accessor.save_file('Tiltfile', tiltfile.getvalue(), overwrite)

  def generate_projects(self, images, file_accessor):
    for imageKey in images.keys():
      print(f'🐳 Generating {imageKey}/Dockerfile...')
      file_accessor.mkdirhier(imageKey)
      dockerfile = f'{imageKey}/Dockerfile'
      file_accessor.save_file(dockerfile, 'FROM scratch\n', False)

  def _get_kubecontext_arg(self, env_accessor):
    e = env_accessor.getenv('KUBEDEV_KUBECONTEXT')
    return f'--kube-context {e}' if e != None and isinstance(e, str) and e != '' else ' '

  def _template_or_deploy(self, kubedev, command, shell_executor, env_accessor, file_accessor):
    variables = KubedevConfig.get_global_variables(kubedev)
    tag = KubedevConfig.get_tag(env_accessor)
    kubeconfig = KubedevConfig.get_kubeconfig_path(env_accessor, file_accessor)
    command = [
        '/bin/sh',
        '-c',
        f'helm {command} ' +
        f'--kubeconfig {kubeconfig} {self._get_kubecontext_arg(env_accessor)} ' +
        f'--set KUBEDEV_TAG="{tag}"' +
        KubedevConfig.get_helm_set_env_args(kubedev)
    ]
    shell_executor.execute(command, variables)

  def template(self, configFileName, shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor(), file_accessor=RealFileAccessor()):
    self.template_from_config(
        self._load_config(configFileName), shell_executor, env_accessor, file_accessor)

  def template_from_config(self, kubedev, shell_executor, env_accessor, file_accessor):
    return self._template_or_deploy(kubedev, "template ./helm-chart/", shell_executor, env_accessor, file_accessor)

  def deploy(self, configFileName, shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor(), file_accessor=RealFileAccessor()):
    self.deploy_from_config(
        self._load_config(configFileName), shell_executor, env_accessor, file_accessor)

  def deploy_from_config(self, kubedev, shell_executor, env_accessor, file_accessor):
    return self._template_or_deploy(kubedev, f"upgrade {kubedev['name']} ./helm-chart/ --install --wait", shell_executor, env_accessor, file_accessor)

  def build(self, configFileName, container, shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor()):
    self.build_from_config(
        self._load_config(configFileName), container=container, shell_executor=shell_executor, env_accessor=env_accessor)

  def build_from_config(self, kubedev, container, shell_executor, env_accessor):
    images = KubedevConfig.get_images(kubedev, env_accessor)
    if not container in images:
      raise KeyError(
          f"Container {container} is not defined in kubedev config.")
    else:
      image = images[container]
      call = [
          '/bin/sh',
          '-c',
          f"docker build -t {image['imageName']} " +
          KubedevConfig.get_docker_build_args(image) +
          f"{image['buildPath']}"
      ]
      shell_executor.execute(call, dict())

  def push(self, configFileName, container, shell_executor=RealShellExecutor(), env_accessor=RealEnvAccessor()):
    self.push_from_config(
        self._load_config(configFileName), container=container, shell_executor=shell_executor, env_accessor=env_accessor)

  def push_from_config(self, kubedev, container, shell_executor, env_accessor):
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
      shell_executor.execute(call, dict())

  def check(self, configFileName, env_accessor=RealEnvAccessor(), printer=RealPrinter()):
    self.check_from_config(
        self._load_config(configFileName), env_accessor=env_accessor, printer=printer)

  def check_from_config(self, kubedev, env_accessor, printer):
    result = True

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

    envs = KubedevConfig.get_all_env_names(kubedev, True, True)
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

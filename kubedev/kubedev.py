import json
import pathlib
from os import getenv, path

import yaml


class RealFileAccessor:
  def load_file(self, filename):
    with open(filename, 'r') as f:
      return f.read()

  def save_file(self, filename, content, overwrite):
    targetDir = path.dirname(path.realpath(filename))
    pathlib.Path(targetDir).mkdir(parents=True, exist_ok=True)
    with open(filename, 'w') as f:
      f.write(content)


class RealEnvAccessor:
  def getenv(self, name):
    return getenv(name)


def _replace_variables(text, variables):
  for key, value in variables.items():
    text = text.replace(f'%%{key}%%', f'{value}')
  return text


def _load_template(file, variables):
  with open(file, 'r') as f:
    return _replace_variables(f.read(), variables)


def _build_final_name(first, second):
  if first == second:
    return first
  else:
    return f'{first}-{second}'


class Kubedev:
  def __init__(self, template_dir):
    """
    Initiates a Kubedev object.

    :param template_dir: The directory where kubedev searches for template files. This is usually installed globally when installing kubedev.
    """
    self.template_dir = template_dir

  def generate(self, configFileName, overwrite=False, file_accessor=RealFileAccessor(), env_accessor=RealEnvAccessor()):
    """
    Loads kubedev.json from the local directory and generates files according to kubedev.json's content.

    :param overwrite: Boolean flag whether to overwrite existing files (True), or keep files untouched (False, default).
    :param file_accessor: An injectable class instance that must implement load_file(self, filename) and save_file(self, filename, content).
                          Used to mock this function for unit tests.
    """
    with open(configFileName) as f:
      kubedev = json.loads(f.read())

    return self.generate_from_config(kubedev, overwrite, file_accessor, env_accessor)

  def generate_from_config(self, kubedev, overwrite, file_accessor, env_accessor):
    """
    Generates files according to the config from the kubedev object, which must be a dict of the structure of a kubedev.json file.

    :param kubedev: A dict that contains the content of a `kubedev.json` file.
    :param overwrite: Boolean flag whether to overwrite existing files (True), or keep files untouched (False, default).
    :param file_accessor: An injectable class instance that must implement load_file(self, filename) and save_file(self, filename, content).
                          Used to mock this function for unit tests.
    """
    projectName = kubedev['name']
    projectDescription = kubedev['description']
    imagePullSecrets = kubedev['imagePullSecrets']
    imageRegistry = kubedev['imageRegistry']
    tag = f'{env_accessor.getenv("CI_COMMIT_SHORT_SHA")}_{env_accessor.getenv("CI_COMMIT_REF_NAME")}'

    variables = {
        'KUBEDEV.PROJECT_NAME': projectName,
        'KUBEDEV.PROJECT_DESCRIPTION': projectDescription,
        'KUBEDEV.IMAGEPULLSECRETS': imagePullSecrets,
        'KUBEDEV.IMAGEREGISTRY': imageRegistry,
        'KUBEDEV.TAG': tag
    }

    envs = kubedev['required-envs'] if 'required-envs' in kubedev else dict()

    chartYamlTemplatePath = path.join(
        self.template_dir, 'helm-chart', 'Chart.yaml')
    file_accessor.save_file(path.join(
        'helm-chart', 'Chart.yaml'), _load_template(chartYamlTemplatePath, variables), overwrite)

    if 'deployments' in kubedev:
      for deploymentName, value in kubedev['deployments'].items():
        finalDeploymentName = _build_final_name(projectName, deploymentName)
        deployEnvs = value['required-envs'] if 'required-envs' in value else dict()
        ports = value['ports'] if 'ports' in value else dict()
        replicas = int(value['replicas']) if 'replicas' in value else 2
        deployVars = {
            'KUBEDEV.DEPLOYMENT_NAME': finalDeploymentName,
            'KUBEDEV.DEPLOYMENT_REPLICAS': replicas,
            **variables
        }
        deploymentTemplatePath = path.join(
            self.template_dir, 'helm-chart', 'deployment.yaml')
        deployment = yaml.safe_load(
            _load_template(deploymentTemplatePath, deployVars))
        allEnvs = {**envs, **deployEnvs}
        containers = [{
            'name': finalDeploymentName,
            'image': f'{imageRegistry}/{finalDeploymentName}:{tag}',
            'env': [
                {
                    'name': envName,
                    'value': f'{{{{.Values.{envName}}}}}'
                } for (envName, envDef) in allEnvs.items()],
            'ports': [
                {
                    'name': portName,
                    'containerPort': value['container']
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
          finalServiceName = _build_final_name(projectName, deploymentName)
          serviceVars = {
              'KUBEDEV.SERVICE_NAME': finalServiceName,
              'KUBEDEV.SERVICE_TYPE': 'ClusterIP',
              **variables
          }
          serviceTemplatePath = path.join(
              self.template_dir, 'helm-chart', 'service.yaml')
          service = yaml.safe_load(
              _load_template(serviceTemplatePath, serviceVars))
          service['ports'] = [
              {
                  'port': port['service'],
                  'targetPort': port['container'],
                  'name': portName
              } for (portName, port) in ports.items() if 'service' in port and 'container' in port
          ]
          service['selector'] = {
              'kubedev-app': projectName,
              'kubedev-deployment': finalDeploymentName
          }
          serviceYamlPath = path.join(
              'helm-chart', 'templates', 'deployments', deploymentName + '_service.yaml')
          file_accessor.save_file(
              serviceYamlPath, yaml.safe_dump(service), overwrite)
    return True

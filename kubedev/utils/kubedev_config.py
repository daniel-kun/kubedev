import os
from string import Template

kubeconfig_temp_path = os.path.join('.kubedev', 'kube_config_tmp')


class KubedevConfig:
  @staticmethod
  def get_global_variables(kubedev):
    return {
        'KUBEDEV_PROJECT_NAME': kubedev['name'],
        'KUBEDEV_PROJECT_DESCRIPTION': kubedev['description'],
        'KUBEDEV_IMAGEPULLSECRETS': kubedev['imagePullSecrets'],
        'KUBEDEV_IMAGEREGISTRY': kubedev['imageRegistry']
    }

  @staticmethod
  def get_all_env_names(kubedev, build, container):
    envs = set(KubedevConfig.load_envs(
        kubedev, build=build, container=container).keys())
    if 'deployments' in kubedev:
      for (_, deployment) in kubedev['deployments'].items():
        deploymentEnvs = KubedevConfig.load_envs(
            deployment, build=build, container=container)
        envs = {
            *envs, *set(deploymentEnvs.keys())}
    return envs

  @staticmethod
  def get_all_app_definitions(kubedev: dict) -> dict:
    def if_exists(obj: dict, field: str) -> dict:
      if field in obj:
        return obj[field]
      else:
        return dict()

    return {
      key: definition for key, definition in {**if_exists(kubedev, 'deployments'), **if_exists(kubedev, 'cronjobs'), **if_exists(kubedev, 'generic')}.items()
    }

  @staticmethod
  def get_helm_set_env_args(kubedev):
    '''
    Returns shell parameters for helm commands in the form of ``--set <variable>="${<variable>}" ...''
    from a kubedev config.
    '''
    envs = KubedevConfig.get_all_env_names(kubedev, False, True)

    if len(envs) > 0:
      return ' ' + ' '.join([f'--set {e}="${{{e}}}"' for e in sorted(envs)])
    else:
      return ''

  @staticmethod
  def get_kubeconfig_path(env_accessor, file_accessor):
    cfg = env_accessor.getenv('KUBEDEV_KUBECONFIG')
    if isinstance(cfg, type(None)):
      raise Exception(
          'Required environment variable ${KUBEDEV_KUBECONFIG} is not defined. Please define it with the content of your .kube/config file that shall be used for deployment.')
    elif cfg == 'default':
      home = env_accessor.getenv('HOME')
      return os.path.join(home, '.kube', 'config')
    else:
      file_accessor.save_file(kubeconfig_temp_path, cfg, True)
      return kubeconfig_temp_path

  @staticmethod
  def load_envs(source, build, container):
    """
    Returns a dict of environment variable definitions from `source', filtered for env vars that
    are declared for build and/or container, depending on `build' and `container's values (True/False).

    :param source: The object that contains a dict of environment variables
    :param build: True, when env vars with either `"build": true' or without a "build" property
    :param container: True, when env vars with either `"container": true' or without a "container" property
    """

    def _use_env(source, use, useField):
      """
      Returns True when use is True and either useField exists in source and is True or useField does not exist in source.
      """
      if useField in source:
        return use and source[useField]
      else:
        return use

    envs = source['required-envs'] if 'required-envs' in source else dict()
    return {key: content for key, content in envs.items() if _use_env(content, build, "build") or _use_env(content, container, "container")}

  @staticmethod
  def get_images(kubedev, env_accessor):
    images = dict()
    globalBuildEnvs = KubedevConfig.load_envs(kubedev, True, False)
    globalContainerEnvs = KubedevConfig.load_envs(kubedev, False, True)
    tag = KubedevConfig.get_tag(env_accessor)
    imageRegistry = kubedev["imageRegistry"]
    name = kubedev["name"]
    globalUsedFrameworks = kubedev["usedFrameworks"] if "usedFrameworks" in kubedev else []
    if "deployments" in kubedev:
      for deploymentKey, deployment in kubedev["deployments"].items():
        finalDeploymentName = KubedevConfig.collapse_names(name, deploymentKey)
        localUsedFrameworks = deployment["usedFrameworks"] if "usedFrameworks" in deployment else []
        usedFrameworks = globalUsedFrameworks + localUsedFrameworks
        images[deploymentKey] = {
            "imageName": f"{imageRegistry}/{finalDeploymentName}:{tag}",
            "imageNameTagless": f"{imageRegistry}/{finalDeploymentName}",
            "buildPath": KubedevConfig.get_buildpath(name, deploymentKey),
            "ports": deployment['ports'] if 'ports' in deployment else dict(),
            "buildEnvs": {*globalBuildEnvs, *KubedevConfig.load_envs(deployment, True, False)},
            "containerEnvs": {*globalContainerEnvs, *KubedevConfig.load_envs(deployment, False, True)},
            "volumes": deployment["volumes"]["dev"] if "volumes" in deployment and "dev" in deployment["volumes"] else dict(),
            "usedFrameworks": usedFrameworks
        }
    return images

  @staticmethod
  def get_buildpath(app_name, image_name):
    if app_name == image_name:
      return "./"
    else:
      return f"./{image_name}/"

  @staticmethod
  def get_tag(env_accessor):
    commit, branch = (env_accessor.getenv('CI_COMMIT_SHORT_SHA'),
                      env_accessor.getenv('CI_COMMIT_REF_NAME'))
    if not isinstance(commit, type(None)) and not isinstance(branch, type(None)):
      return f'{commit}_{branch}'
    else:
      return 'none'  # When outside of the CI environment, the tag usually will be overwritten by tilt anyways, so it is irrelevant

  @staticmethod
  def collapse_names(first, second):
    if first == second:
      return first
    else:
      return f'{first}-{second}'

  @staticmethod
  def get_docker_build_args(image):
    """
    Returns a string with all "--build-arg ..." parameters to the "docker build ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    envs = image['buildEnvs']
    return " ".join([f'--build-arg {env}="${{{env}}}"' for env in sorted(envs)]) + " "

  @staticmethod
  def get_docker_run_envs(image):
    """
    Returns a string with all "--env ..." parameters to the "docker run ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    envs = image['containerEnvs']
    return " ".join([f'--env {env}="${{{env}}}"' for env in sorted(envs)]) + " "

  @staticmethod
  def get_docker_run_volumes(image, file_accessor, shell_executor):
    """
    Returns a string with all "--volume ..." parameters to the "docker run ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    def create_and_normalize(path):
      file_accessor.mkdirhier(path)
      procVersion = file_accessor.load_file('/proc/version')
      if "Microsoft" in procVersion:
        return shell_executor.get_output(['wslpath', '-aw', path]).rstrip('\n').replace('\\', '\\\\')
      else:
        return os.path.abspath(path)

    volumes = image["volumes"]
    return " ".join([
      f"--volume {create_and_normalize(hostPath)}:{containerPath}" for hostPath, containerPath in volumes.items()
    ]) + (" " if len(volumes) > 0 else "")

  @staticmethod
  def get_docker_run_ports(image):
    """
    Returns a string with all "--publish ..." parameters to the "docker run ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    return " ".join([
      f"--publish {port['dev']}:{port['container']}" for port in image['ports'].values() if "container" in port and "dev" in port
    ]) + " "

  @staticmethod
  def get_helm_release_name(kubedev):
    if 'helmReleaseName' in kubedev:
      return kubedev['helmReleaseName']
    else:
      return kubedev['name']

  @staticmethod
  def expand_variables(text: str, env_accessor, variables: dict = dict()) -> str:
    return Template(text).substitute({**env_accessor.environ(), **variables})

import itertools
import os
from base64 import b64decode, b64encode
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
  def get_all_envs(kubedev, build, container):
    envs = KubedevConfig.load_envs(
        kubedev, build=build, container=container)
    if 'deployments' in kubedev:
      for (_, deployment) in kubedev['deployments'].items():
        deploymentEnvs = KubedevConfig.load_envs(
            deployment, build=build, container=container)
        envs = {**envs, **deploymentEnvs}
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
  def prepare_envs(envs: dict, env_accessor: object) -> tuple:
    def is_base64(attribs: dict) -> bool:
      return 'transform' in attribs and attribs['transform'] == 'base64'

    def env_name(name: str, attribs: dict) -> str:
      if 'transform' in attribs and attribs['transform'] == 'base64':
        return f'{name}_AS_BASE64'
      else:
        return name

    sortedEnvs = dict(sorted(envs.items()))
    return (
      {name: {**attribs, **{'targetName': env_name(name, attribs)}} for name, attribs in sortedEnvs.items()},
      {env_name(name, attribs): b64encode(env_accessor.getenv(name, default="").encode('utf-8')) for name, attribs in sortedEnvs.items() if is_base64(attribs)}
    )

  @staticmethod
  def get_helm_set_env_args(kubedev: dict, env_accessor: object) -> dict:
    '''
    Returns shell parameters for helm commands in the form of ``--set <variable>="${<variable>}" ...''
    from a kubedev config.
    '''
    (envs, extraEnvs) = KubedevConfig.prepare_envs(KubedevConfig.get_all_envs(kubedev, False, True), env_accessor=env_accessor)

    if len(envs) > 0:
      return {
        'cmdline': ' ' + ' '.join([f'--set {name}="${{{attribs["targetName"]}}}"' for name, attribs in envs.items()]),
        'envs': extraEnvs
      }
    else:
      return {
        'cmdline': '',
        'envs': dict()
      }

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
            "buildEnvs": {**globalBuildEnvs, **KubedevConfig.load_envs(deployment, True, False)},
            "containerEnvs": {**globalContainerEnvs, **KubedevConfig.load_envs(deployment, False, True)},
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
  def get_docker_build_args(image: dict, env_accessor: object) -> tuple:
    """
    Returns a string with all "--build-arg ..." parameters to the "docker build ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    (envs, extraEnvs) = KubedevConfig.prepare_envs(image['buildEnvs'], env_accessor=env_accessor)
    return (
      " ".join([f'--build-arg {name}="${{{attribs["targetName"]}}}"' for name, attribs in sorted(envs.items())]) + " ",
      extraEnvs
    )

  @staticmethod
  def get_docker_run_envs(image: dict, env_accessor: object) -> tuple:
    """
    Returns a string with all "--env ..." parameters to the "docker run ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    (envs, extraEnvs) = KubedevConfig.prepare_envs(image['containerEnvs'], env_accessor)
    return (
      " ".join([f'--env {name}="${{{attribs["targetName"]}}}"' for name, attribs in sorted(envs.items())]) + " ",
      extraEnvs
    )

  @staticmethod
  def get_docker_run_volumes_list(image, file_accessor, shell_executor):
    """
    Returns a string with all "--volume ..." parameters to the "docker run ..." call.

    :param image: One entry returned from KubedevConfig.get_images()
    """
    def create_and_normalize(path: str) -> str:
      procFile = file_accessor.load_file('/proc/version')
      procVersion = procFile if procFile is not None else ""
      if "Microsoft" in procVersion:
        return shell_executor.get_output(['wslpath', '-aw', path]).rstrip('\n').replace('\\', '\\\\')
      else:
        return file_accessor.abspath(path)

    def get_path(hostPath, containerPathSpec) -> str:
      if type(containerPathSpec) is dict:
        if 'path' in containerPathSpec:
          path = containerPathSpec['path']
          if 'content' in containerPathSpec:
            tempFilePath = os.path.join('.kubedev', f'temp_{hostPath}')
            file_accessor.save_file(tempFilePath, content=containerPathSpec['content'], overwrite=True)
            effectiveHostPath = create_and_normalize(tempFilePath)
          elif 'base64' in containerPathSpec:
            tempFilePath = os.path.join('.kubedev', f'temp_{hostPath}')
            file_accessor.save_file(tempFilePath, content=b64decode(containerPathSpec['base64']).decode('utf-8'), overwrite=True)
            effectiveHostPath = create_and_normalize(os.path.join('.kubedev', f'temp_{hostPath}'))
          else:
            effectiveHostPath = create_and_normalize(hostPath)
          suffix = ':ro' if 'readOnly' in containerPathSpec and containerPathSpec['readOnly'] == True else ''
          return f'{effectiveHostPath}:{path}{suffix}'
        else:
          raise Exception('Volume specification does not contain required "path" attribute')
      elif type(containerPathSpec) is str:
        return f"{create_and_normalize(hostPath)}:{containerPathSpec}"
      else:
        raise Exception(f'Volume specification must either be a string, or an object with an "path" property, but is {type(containerPathSpec)} instead.')

    volumes = image["volumes"] if "volumes" in image else dict()
    return list(itertools.chain(*[["--volume", get_path(hostPath, containerPath)] for hostPath, containerPath in volumes.items()]))

  @staticmethod
  def get_docker_run_volumes(image, file_accessor, shell_executor):
    args = KubedevConfig.get_docker_run_volumes_list(image, file_accessor, shell_executor)
    return " ".join(args) + (" " if len(args) > 0 else "")

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

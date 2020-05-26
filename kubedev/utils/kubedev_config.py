import os

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
    globalEnvs = KubedevConfig.load_envs(kubedev, True, False)
    tag = KubedevConfig.get_tag(env_accessor)
    imageRegistry = kubedev["imageRegistry"]
    name = kubedev["name"]
    if "deployments" in kubedev:
      for deploymentKey, deployment in kubedev["deployments"].items():
        finalDeploymentName = KubedevConfig.collapse_names(name, deploymentKey)
        images[deploymentKey] = {
            "imageName": f"{imageRegistry}/{finalDeploymentName}:{tag}",
            "buildPath": KubedevConfig.get_buildpath(name, deploymentKey),
            "required-envs": {*globalEnvs, *KubedevConfig.load_envs(deployment, True, False)}
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
    envs = image['required-envs']
    return " ".join([f'--build-arg {env}="${{{env}}}"' for env in sorted(envs)]) + " "

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
  def get_helm_set_env_args(kubedev):
    '''
    Returns shell parameters for helm commands in the form of ``--set <variable>="${<variable>}" ...''
    from a kubedev config. 
    '''
    if 'required-envs' in kubedev:
      envs = set(kubedev['required-envs'].keys())
    else:
      envs = set()
    if 'deployments' in kubedev:
      for (_, deployment) in kubedev['deployments'].items():
        if 'required-envs' in deployment:
          envs = {*envs, *set(deployment['required-envs'].keys())}

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

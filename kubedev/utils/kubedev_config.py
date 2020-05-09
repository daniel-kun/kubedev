import os


class KubedevConfig:
  @staticmethod
  def get_set_env_args(kubedev):
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
  def get_kubeconfig_path(env_accessor):
    cfg = env_accessor.getenv('KUBEDEV_KUBECONFIG')
    if isinstance(cfg, type(None)):
      raise Exception(
          'Required environment variable ${KUBEDEV_KUBECONFIG} is not defined. Please defined it with the content of your .kube/config file that shall be used for deployment.')
    elif cfg == 'default':
      home = env_accessor.getenv('HOME')
      return os.path.join(home, '.kube', 'config')
    else:
      raise NotImplementedError(
          'Writing content of ${KUBEDEV_KUBECONFIG} to temporary file is not yet implemented.')

import unittest

from kubedev.utils import KubedevConfig, kubeconfig_temp_path
from test_utils import EnvMock, FileMock, testDeploymentConfig


class KubedevConfigTests(unittest.TestCase):

  def test_get_helm_set_env_args(self):
    envs = KubedevConfig.get_helm_set_env_args(testDeploymentConfig)
    self.assertEqual(' --set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" --set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                     envs)

  def test_get_kubeconfig_path_default(self):
    envs = EnvMock()
    envs.setenv('KUBEDEV_KUBECONFIG', 'default')
    envs.setenv('HOME', '/home/kubedev')
    files = FileMock()

    kubecfg = KubedevConfig.get_kubeconfig_path(envs, files)
    self.assertEqual('/home/kubedev/.kube/config', kubecfg)

  def test_get_kubeconfig_path_env_not_set(self):
    envs = EnvMock()
    files = FileMock()
    self.assertRaises(
        Exception, lambda x: KubedevConfig.get_kubeconfig_path(envs, files))

  def test_get_kubeconfig_path_with_kubedev_kubeconfig_set(self):
    envs = EnvMock()
    kubeConfigContent = '''some:
  kubeconfig: file
'''
    envs.setenv('KUBEDEV_KUBECONFIG', kubeConfigContent)
    files = FileMock()
    kubeConfigPath = KubedevConfig.get_kubeconfig_path(envs, files)
    self.assertEqual(kubeconfig_temp_path, kubeConfigPath)
    kubeConfig = files.load_file(kubeConfigPath)
    self.assertEqual(kubeConfig, kubeConfigContent)

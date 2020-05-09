import unittest

from kubedev.utils import KubedevConfig
from test_utils import EnvMock, testDeploymentConfig


class KubedevConfigTests(unittest.TestCase):

  def test_get_set_env_args(self):
    envs = KubedevConfig.get_set_env_args(testDeploymentConfig)
    self.assertEqual(' --set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" --set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                     envs)

  def test_get_kubeconfig_path_default(self):
    envs = EnvMock()
    envs.setenv('KUBEDEV_KUBECONFIG', 'default')
    envs.setenv('HOME', '/home/kubedev')
    kubecfg = KubedevConfig.get_kubeconfig_path(envs)
    self.assertEqual('/home/kubedev/.kube/config', kubecfg)

  def test_get_kubeconfig_path_env_not_set(self):
    envs = EnvMock()
    self.assertRaises(
        Exception, lambda x: KubedevConfig.get_kubeconfig_path(envs))

  def test_get_kubeconfig_path_with_kubedev_kubeconfig_set(self):
    envs = EnvMock()
    envs.setenv('KUBEDEV_KUBECONFIG', 'default')
    kubecfg = KubedevConfig.get_kubeconfig_path(envs)
    self.assertEqual('.kubedev/kube_config_tmp', kubecfg)

import unittest

from kubedev.utils import KubedevConfig, kubeconfig_temp_path
from test_utils import (EnvMock, FileMock, testDeploymentConfig,
                        testMultiDeploymentsConfig)


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

  def test_get_images(self):
    images = KubedevConfig.get_images(
        testMultiDeploymentsConfig, env_accessor=EnvMock())
    self.assertIn("foo-deploy", images)
    fooDeploy = images["foo-deploy"]
    self.assertIn("buildEnvs", fooDeploy)

    fooBuildEnvs = fooDeploy["buildEnvs"]
    self.assertIn("FOO_SERVICE_GLOBAL_ENV2", fooBuildEnvs)
    self.assertIn("FOO_SERVICE_DEPLOY_ENV1", fooBuildEnvs)
    self.assertEqual(2, len(fooBuildEnvs))

    self.assertIn("containerEnvs", fooDeploy)
    fooContainerEnvs = fooDeploy["containerEnvs"]
    self.assertIn("FOO_SERVICE_GLOBAL_ENV1", fooContainerEnvs)
    self.assertIn("FOO_SERVICE_GLOBAL_ENV2", fooContainerEnvs)
    self.assertIn("FOO_SERVICE_DEPLOY_ENV1", fooContainerEnvs)
    self.assertIn("FOO_SERVICE_DEPLOY_ENV2", fooContainerEnvs)
    self.assertEqual(4, len(fooContainerEnvs))

    self.assertIn("imageName", fooDeploy)
    self.assertEqual(
        "foo-registry/foo-service-foo-deploy:none", fooDeploy["imageName"])
    self.assertIn("buildPath", fooDeploy)
    self.assertEqual("./foo-deploy/", fooDeploy["buildPath"])

    self.assertIn("bar-deploy", images)
    barDeploy = images["bar-deploy"]
    self.assertIn("buildEnvs", barDeploy)

    barBuildEnvs = barDeploy["buildEnvs"]
    self.assertIn("FOO_SERVICE_GLOBAL_ENV2", barBuildEnvs)
    self.assertIn("BAR_SERVICE_DEPLOY_ENV2", barBuildEnvs)
    self.assertEqual(2, len(barBuildEnvs))

    self.assertIn("imageName", barDeploy)
    self.assertEqual(
        "foo-registry/foo-service-bar-deploy:none", barDeploy["imageName"])
    self.assertIn("buildPath", barDeploy)
    self.assertEqual("./bar-deploy/", barDeploy["buildPath"])

  def test_get_images_collapsed(self):
    config = testDeploymentConfig.copy()
    config['name'] = 'foo-deploy'
    images = KubedevConfig.get_images(config, env_accessor=EnvMock())
    self.assertIn('foo-deploy', images)
    deploy = images['foo-deploy']
    self.assertIn('imageName', deploy)
    self.assertEqual('foo-registry/foo-deploy:none', deploy['imageName'])
    self.assertIn('buildPath', deploy)
    self.assertEqual('./', deploy['buildPath'])

  def test_get_images_in_ci(self):
    self.skipTest("Test must be implemented")

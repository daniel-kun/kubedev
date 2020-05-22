import unittest

import yaml
from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, OutputMock, ShellExecutorMock,
                        testDeploymentConfig, testMultiDeploymentsConfig)


def _set_all_envs(env):
  env.setenv('FOO_SERVICE_GLOBAL_ENV1', 'g1')
  env.setenv('FOO_SERVICE_GLOBAL_ENV2', 'g2')
  env.setenv('FOO_SERVICE_DEPLOY_ENV1', 'd1')
  env.setenv('FOO_SERVICE_DEPLOY_ENV2', 'd2')
  env.setenv('BAR_SERVICE_DEPLOY_ENV1', 'b1')
  env.setenv('BAR_SERVICE_DEPLOY_ENV2', 'b2')


class KubeDevCheckTests(unittest.TestCase):

  def test_check_env_multi_deployment_all_set(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testMultiDeploymentsConfig, env_accessor=envMock, printer=outputMock)

    self.assertTrue(result)
    messages = outputMock.messages()
    self.assertEqual(0, len(messages))

  def test_check_env_multi_deployment_one_missing(self):
    envMock = EnvMock()
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV1', 'g1')
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV2', 'g2')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV1', 'd1')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV2', 'd2')
    envMock.setenv('BAR_SERVICE_DEPLOY_ENV1', 'b1')
    outputMock = OutputMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testMultiDeploymentsConfig, env_accessor=envMock, printer=outputMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    self.assertEqual(1, len(messages))
    self.assertIn('not defined', messages[0]['message'].lower())

  def test_check_env_multi_deployment_multiple_missing(self):
    envMock = EnvMock()
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV1', 'g1')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV2', 'd2')
    envMock.setenv('BAR_SERVICE_DEPLOY_ENV1', 'b1')
    outputMock = OutputMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testMultiDeploymentsConfig, env_accessor=envMock, printer=outputMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    self.assertEqual(3, len(messages))
    self.assertIn('not defined', messages[0]['message'].lower())

  def test_check_image_registry_missing(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()

    config = testMultiDeploymentsConfig.copy()
    del config['imageRegistry']

    sut = Kubedev()
    result = sut.check_from_config(
        config, env_accessor=envMock, printer=outputMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    # Verify that the error message contains the string 'imageRegistry'
    self.assertIn('imageRegistry', messages[0]["message"])

  def test_check_image_pullsecrets_missing(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()

    config = testMultiDeploymentsConfig.copy()
    del config['imagePullSecrets']

    sut = Kubedev()
    result = sut.check_from_config(
        config, env_accessor=envMock, printer=outputMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    # Verify that the error message contains the string 'imagePullSecrets'
    self.assertIn('imagePullSecrets', messages[0]["message"])

  def test_check_name_missing(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()

    config = testMultiDeploymentsConfig.copy()
    del config['name']

    sut = Kubedev()
    result = sut.check_from_config(
        config, env_accessor=envMock, printer=outputMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    # Verify that the error message contains the string 'name'
    self.assertIn('name', messages[0]["message"])

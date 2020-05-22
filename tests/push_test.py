import unittest

import yaml
from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig, testMultiDeploymentsConfig)


class KubeDevPushTests(unittest.TestCase):

  def test_push_multi_deployment_foo(self):
    envMock = EnvMock()
    envMock.setenv('SHELL', '/bin/bash')
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    sut.build_from_config(testMultiDeploymentsConfig, 'foo-deploy',
                          shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/bash',
        '-c',
        'docker push foo-registry/foo-service-foo-deploy:none'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_push_multi_deployment_bar(self):
    envMock = EnvMock()
    envMock.setenv('SHELL', '/bin/bash')
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    sut.push_from_config(testMultiDeploymentsConfig, 'bar-deploy',
                         shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/bash',
        '-c',
        'docker push foo-registry/foo-service-bar-deploy:none'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_push_invalid_container(self):
    envMock = EnvMock()
    envMock.setenv('SHELL', '/bin/bash')
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    self.assertRaises(KeyError, lambda: sut.build_from_config(testMultiDeploymentsConfig, 'i-do-not-exist',
                                                              shell_executor=shellMock, env_accessor=envMock))

  def test_push_single_collapsedname_deployment_foo(self):
    envMock = EnvMock()
    envMock.setenv('SHELL', '/bin/bash')
    shellMock = ShellExecutorMock()
    config = testDeploymentConfig.copy()
    # Set the global app name to the same name as the deployment,
    # and have only this deployment in the config. In this special case everything
    # will be collapsed to the project root directory, in order not to clutter
    # the project's repo with sub-directories
    config['name'] = 'foo-deploy'

    sut = Kubedev()
    sut.push_from_config(config, 'foo-deploy',
                         shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    print(calls[0]["cmd"])
    self.assertListEqual([
        '/bin/bash',
        '-c',
        'docker push foo-registry/foo-deploy:none'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

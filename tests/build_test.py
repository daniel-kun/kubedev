import unittest

import yaml
from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig, testMultiDeploymentsConfig)


class KubeDevBuildTests(unittest.TestCase):

  def test_build_multi_deployment_foo(self):
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
        'docker ' +
        'build ' +
        '-t foo-registry/foo-service-foo-deploy:none ' +
        '--build-arg ' +
        'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" ' +
        '--build-arg ' +
        'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
        './foo-deploy/'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_build_multi_deployment_bar(self):
    envMock = EnvMock()
    envMock.setenv('SHELL', '/bin/bash')
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    sut.build_from_config(testMultiDeploymentsConfig, 'bar-deploy',
                          shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/bash',
        '-c',
        'docker ' +
        'build ' +
        '-t foo-registry/foo-service-bar-deploy:none ' +
        '--build-arg ' +
        'BAR_SERVICE_DEPLOY_ENV2="${BAR_SERVICE_DEPLOY_ENV2}" ' +
        '--build-arg ' +
        'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
        './bar-deploy/'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_build_invalid_container(self):
    envMock = EnvMock()
    envMock.setenv('SHELL', '/bin/bash')
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    self.assertRaises(KeyError, lambda: sut.build_from_config(testMultiDeploymentsConfig, 'i-do-not-exist',
                                                              shell_executor=shellMock, env_accessor=envMock))

  def test_build_single_collapsedname_deployment_foo(self):
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
    sut.build_from_config(config, 'foo-deploy',
                          shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/bash',
        '-c',
        'docker ' +
        'build ' +
        '-t foo-registry/foo-deploy:none ' +
        '--build-arg ' +
        'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" ' +
        '--build-arg ' +
        'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
        '--build-arg ' +
        'FOO_SERVICE_DEPLOY_ENV3="${FOO_SERVICE_DEPLOY_ENV3}" ' +
        '--build-arg ' +
        'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" ' +
        '--build-arg ' +
        'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
        './'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

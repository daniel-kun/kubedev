import unittest

import yaml
from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig, testMultiDeploymentsConfig)


class KubeDevPushTests(unittest.TestCase):

  def test_push_multi_deployment_foo(self):
    envMock = EnvMock()
    fileMock = FileMock()
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    sut.push_from_config(testMultiDeploymentsConfig, 'foo-deploy',
                         file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'docker push foo-registry/foo-service-foo-deploy:none'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_push_multi_deployment_bar(self):
    envMock = EnvMock()
    fileMock = FileMock()
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    sut.push_from_config(testMultiDeploymentsConfig, 'bar-deploy',
                         file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'docker push foo-registry/foo-service-bar-deploy:none'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_push_invalid_container(self):
    envMock = EnvMock()
    fileMock = FileMock()
    shellMock = ShellExecutorMock()

    sut = Kubedev()
    self.assertRaises(KeyError, lambda: sut.push_from_config(testMultiDeploymentsConfig, 'i-do-not-exist',
                                                              file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock))

  def test_push_single_collapsedname_deployment_foo(self):
    envMock = EnvMock()
    fileMock = FileMock()
    shellMock = ShellExecutorMock()
    config = testDeploymentConfig.copy()
    # Set the global app name to the same name as the deployment,
    # and have only this deployment in the config. In this special case everything
    # will be collapsed to the project root directory, in order not to clutter
    # the project's repo with sub-directories
    config['name'] = 'foo-deploy'

    sut = Kubedev()
    sut.push_from_config(config, 'foo-deploy',
                         file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock)

    calls = shellMock.calls()
    self.assertGreaterEqual(len(calls), 1)
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'docker push foo-registry/foo-deploy:none'
    ], calls[0]['cmd'])
    self.assertEqual(1, len(calls))

  def test_push_creates_docker_config_json_if_not_exists_and_env_vars_are_set(self):
    envMock = EnvMock()
    envMock.setenv('HOME', '/home/user')
    envMock.setenv('CI', 'yes')
    envMock.setenv('DOCKER_AUTH_CONFIG', '{e93e908c-e490-40d9-b6b2-0ca899a3a2d3}')
    fileMock = FileMock()
    shellMock = ShellExecutorMock()
    config = testDeploymentConfig.copy()
    config['name'] = 'foo-deploy'

    sut = Kubedev()
    sut.push_from_config(config, 'foo-deploy', file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock)

    self.assertIsNotNone(fileMock.load_file('/home/user/.docker/config.json'))

  def test_push_does_not_create_docker_config_json_if_not_exists_but_env_vars_are_not_set(self):
    envMock = EnvMock()
    envMock.setenv('HOME', '/home/user')
    fileMock = FileMock()
    shellMock = ShellExecutorMock()
    config = testDeploymentConfig.copy()
    config['name'] = 'foo-deploy'

    sut = Kubedev()
    sut.push_from_config(config, 'foo-deploy', file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock)

    self.assertIsNone(fileMock.load_file('/home/user/.docker/config.json'))

  def test_push_does_not_overwrite_existing_docker_config_json(self):
    envMock = EnvMock()
    envMock.setenv('HOME', '/home/user')
    fileMock = FileMock()
    fileMock.save_file('/home/user/.docker/config.json', '{767276df-c470-49b5-9904-495806233204}', overwrite=True)
    shellMock = ShellExecutorMock()
    config = testDeploymentConfig.copy()
    config['name'] = 'foo-deploy'

    sut = Kubedev()
    sut.push_from_config(config, 'foo-deploy', file_accessor=fileMock, shell_executor=shellMock, env_accessor=envMock)

    self.assertEqual(fileMock.load_file('/home/user/.docker/config.json'), '{767276df-c470-49b5-9904-495806233204}')

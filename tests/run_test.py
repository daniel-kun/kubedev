import unittest

from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, OutputMock, ShellExecutorMock,
                        TagGeneratorMock, testDeploymentConfig,
                        testMultiDeploymentsConfig)


class KubeDevRunTests(unittest.TestCase):

  def test_run_multi_with_foo_deploy_with_tty(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=True)
    outputMock = OutputMock()
    files = FileMock()
    mockTag = 'slkdjf19'
    tagGeneratorMock = TagGeneratorMock([mockTag])

    sut = Kubedev()

    returnCode = sut.run_from_config(testMultiDeploymentsConfig, 'foo-deploy', env_accessor=envMock,
                                     shell_executor=shell, printer=outputMock, file_accessor=files, tag_generator=tagGeneratorMock)

    self.assertEqual(returnCode, 0)
    calls = shell.calls()
    self.assertGreaterEqual(len(calls), 2)
    self.assertListEqual(calls[0]['cmd'], [
      '/bin/sh',
      '-c',
      'docker ' +
      'build ' +
      '-t ' +
      f'foo-registry/foo-service-foo-deploy:{mockTag} ' +
      '--build-arg ' +
      'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" ' +
      '--build-arg ' +
      'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
      './foo-deploy/'
    ])
    print(calls[1]['cmd'])
    self.assertListEqual(calls[1]['cmd'], [
        '/bin/sh',
        '-c',
        'docker ' +
        'run ' +
        '--interactive ' +
        '--tty ' +
        '--rm ' +
        '--publish ' +
        '8083:8081 ' +
        '--publish ' +
        '8643:8443 ' +
        '--env ' +
        'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" ' +
        '--env ' +
        'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
        '--env ' +
        'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" ' +
        '--env ' +
        'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
        f'foo-registry/foo-service-foo-deploy:{mockTag}'
    ])

  def test_run_multi_with_foo_deploy_without_tty(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=False)
    outputMock = OutputMock()
    files = FileMock()
    mockTag = 'slkdjf19'
    tagGeneratorMock = TagGeneratorMock([mockTag])

    sut = Kubedev()

    returnCode = sut.run_from_config(testMultiDeploymentsConfig, 'foo-deploy', env_accessor=envMock,
                                     shell_executor=shell, printer=outputMock, file_accessor=files, tag_generator=tagGeneratorMock)

    self.assertEqual(returnCode, 0)
    calls = shell.calls()
    self.assertGreaterEqual(len(calls), 2)
    self.assertListEqual(calls[0]['cmd'], [
      '/bin/sh',
      '-c',
      'docker ' +
      'build ' +
      '-t ' +
      f'foo-registry/foo-service-foo-deploy:{mockTag} ' +
      '--build-arg ' +
      'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" ' +
      '--build-arg ' +
      'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
      './foo-deploy/'
    ])
    print(calls[1]['cmd'])
    self.assertListEqual(calls[1]['cmd'], [
        '/bin/sh',
        '-c',
        'docker ' +
        'run ' +
        '--rm ' +
        '--publish ' +
        '8083:8081 ' +
        '--publish ' +
        '8643:8443 ' +
        '--env ' +
        'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" ' +
        '--env ' +
        'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
        '--env ' +
        'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" ' +
        '--env ' +
        'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}" ' +
        f'foo-registry/foo-service-foo-deploy:{mockTag}'
    ])

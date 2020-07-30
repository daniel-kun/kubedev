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
        '--interactive ' +
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



  def test_run_single_with_volumes_without_tty_in_wsl(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=False, cmd_output='C:\\Projects\\kubedev\\output_docker\n')
    outputMock = OutputMock()
    files = FileMock()
    # Simulate WSL:
    files.save_file('/proc/version', 'Linux version 4.4.0-19041-Microsoft (Microsoft@Microsoft.com) (gcc version 5.4.0 (GCC) ) #1-Microsoft Fri Dec 06 14:06:00 PST 2019', True)
    mockTag = 'slkdjf19'
    tagGeneratorMock = TagGeneratorMock([mockTag])

    sut = Kubedev()

    returnCode = sut.run_from_config(testDeploymentConfig, 'foo-deploy', env_accessor=envMock,
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
      'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
      '--build-arg ' +
      'FOO_SERVICE_DEPLOY_ENV3="${FOO_SERVICE_DEPLOY_ENV3}" ' +
      '--build-arg ' +
      'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" ' +
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
        '--rm ' +
        '--volume C:\\\\Projects\\\\kubedev\\\\output_docker:/test/output ' +
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
        f'foo-registry/foo-service-foo-deploy:{mockTag}'
    ])

import unittest
from copy import deepcopy

from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, OutputMock, ShellExecutorMock,
                        TagGeneratorMock, testDeploymentConfig,
                        testGlobalBase64EnvConfig, testMultiDeploymentsConfig)


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



  def test_run_single_with_volumes_shorthand_without_tty_in_wsl(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=False, cmd_output=['C:\\Projects\\kubedev\\output_docker\n'])
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
    self.assertListEqual(calls[2]['cmd'], [
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

  def test_run_single_with_volumes_read_only(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=False, cmd_output=['C:\\Projects\\kubedev\\output_docker\n'])
    outputMock = OutputMock()
    files = FileMock()
    # Simulate WSL:
    files.save_file('/proc/version', 'Linux version 4.4.0-19041-Microsoft (Microsoft@Microsoft.com) (gcc version 5.4.0 (GCC) ) #1-Microsoft Fri Dec 06 14:06:00 PST 2019', True)
    mockTag = 'slkdjf19'
    tagGeneratorMock = TagGeneratorMock([mockTag])

    sut = Kubedev()

    config = deepcopy(testDeploymentConfig)
    config['deployments']['foo-deploy']['volumes']['dev']['output_docker'] = {
      'path': '/test/output',
      'readOnly': True
    }
    returnCode = sut.run_from_config(config, 'foo-deploy', env_accessor=envMock,
                                     shell_executor=shell, printer=outputMock, file_accessor=files, tag_generator=tagGeneratorMock)

    self.assertEqual(returnCode, 0)
    calls = shell.calls()
    self.assertGreaterEqual(len(calls), 2)
    self.assertListEqual(calls[2]['cmd'], [
        '/bin/sh',
        '-c',
        'docker ' +
        'run ' +
        '--interactive ' +
        '--rm ' +
        '--volume C:\\\\Projects\\\\kubedev\\\\output_docker:/test/output:ro ' +
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

  def test_run_single_with_volumes_with_raw_content_read_only(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=False, cmd_output=['.kubedev\\temp_hello_world\n'])
    outputMock = OutputMock()
    files = FileMock()
    # Simulate WSL:
    files.save_file('/proc/version', 'Linux version 4.4.0-19041-Microsoft (Microsoft@Microsoft.com) (gcc version 5.4.0 (GCC) ) #1-Microsoft Fri Dec 06 14:06:00 PST 2019', True)
    mockTag = 'slkdjf19'
    tagGeneratorMock = TagGeneratorMock([mockTag])

    sut = Kubedev()

    config = deepcopy(testDeploymentConfig)
    config['deployments']['foo-deploy']['volumes']['dev'] = {
        'hello_world': {
            'path': '/test/hello_world.txt',
            'content': 'Hello, World!',
            'readOnly': True
        }
    }
    returnCode = sut.run_from_config(config, 'foo-deploy', env_accessor=envMock,
                                     shell_executor=shell, printer=outputMock, file_accessor=files, tag_generator=tagGeneratorMock)

    self.assertEqual(returnCode, 0)
    calls = shell.calls()
    self.assertGreaterEqual(len(calls), 2)
    self.assertEqual(files.load_file('.kubedev\\temp_hello_world'), 'Hello, World!')
    self.assertListEqual(calls[2]['cmd'], [
        '/bin/sh',
        '-c',
        'docker ' +
        'run ' +
        '--interactive ' +
        '--rm ' +
        '--volume .kubedev\\\\temp_hello_world:/test/hello_world.txt:ro ' +
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

  def test_run_transforms_global_required_env_to_base64(self):
    envMock = EnvMock()
    shell = ShellExecutorMock(is_tty=False, cmd_output=['C:\\Projects\\kubedev\\output_docker\n'])
    outputMock = OutputMock()
    files = FileMock()
    mockTag = 'slkdjf19'
    tagGeneratorMock = TagGeneratorMock([mockTag])

    sut = Kubedev()

    returnCode = sut.run_from_config(testGlobalBase64EnvConfig, 'foo-deploy', env_accessor=envMock,
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
      'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1_AS_BASE64}" ' +
      './foo-deploy/'
    ])
    self.assertIn('FOO_SERVICE_GLOBAL_ENV1_AS_BASE64', calls[0]['env'])
    self.assertListEqual(calls[1]['cmd'], [
        '/bin/sh',
        '-c',
        'docker ' +
        'run ' +
        '--interactive ' +
        '--rm  ' +
        '--env ' +
        'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1_AS_BASE64}" ' +
        f'foo-registry/foo-service-foo-deploy:{mockTag}'
    ])
    self.assertIn('FOO_SERVICE_GLOBAL_ENV1_AS_BASE64', calls[1]['env'])

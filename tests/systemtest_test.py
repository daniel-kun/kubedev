import copy
import unittest

from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock, SleepMock,
                        TagGeneratorMock, configDeploymentBase64Env,
                        configGlobalBase64Env, testDeploymentConfig)


class KubeDevSystemTestTests(unittest.TestCase):
    def test_systemtest_build_without_args(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testDeploymentConfig)
        del config['deployments']['foo-deploy']['systemTest']['testContainer']['buildArgs']
        result = sut.system_test_from_config(config, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        self.assertIn([
            "/bin/sh", "-c", " ".join([
                "docker",
                "build",
                "-t",
                "local-foo-deploy-system-tests-abcd",
                "./systemTests/foo-deploy/"
            ])
        ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_build_with_build_args(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock()
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testDeploymentConfig)
        del config['deployments']['foo-deploy']['systemTest']['services']
        result = sut.system_test_from_config(config, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        self.assertIn([
            "/bin/sh", "-c", " ".join([
                "docker",
                "build",
                "-t",
                "local-foo-deploy-system-tests-abcd",
                "--build-args",
                'FOO_DEPLOY_TESTBUILD_A="a"',
                "./systemTests/foo-deploy/"
            ])
        ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_without_services(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        # Check for running of the test container:
        self.assertIn([
              "/bin/sh",
              "-c",
              " ".join([
                  "docker",
                  "run",
                  "--rm",
                  "--network", 'local-foo-deploy-system-tests-abcd',
                  "--name", "foo-deploy-system-tests-abcd",
                  "--interactive",
                  "--env",
                  'FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}"',
                  "--env",
                  'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}"',
                  "--env",
                  'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                  "--env",
                  'FOO_DEPLOY_TEST_X="X"',
                  "--env",
                  'FOO_DEPLOY_TEST_Y="Y"',
                  "--env",
                  'FOO_DEPLOY_TEST_Z="Z"',
                  "local-foo-deploy-system-tests-abcd"
                  ])
        ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_creates_network_before_run(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        # Check for running of the test container:
        self.assertIn([
                  "docker",
                  "network",
                  "create",
                  "local-foo-deploy-system-tests-abcd"
            ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_fails_when_service_does_not_have_hostname(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock()
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testDeploymentConfig)
        del config['deployments']['foo-deploy']['systemTest']['services']['{foo-deploy}']['hostname']
        result = sut.system_test_from_config(config, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 1)

    def test_systemtest_run_tries_to_remove_services_before_run(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        self.assertIn([
                  "docker",
                  "rm",
                  "--force",
                  "foo-deploy-test"
            ], [call['cmd'] for call in shellMock._calls])
        self.assertIn([
                  "docker",
                  "rm",
                  "--force",
                  "postgres-test"
            ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_with_service_from_registry_with_variables(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testDeploymentConfig)
        del config['deployments']['foo-deploy']['systemTest']['services']['{foo-deploy}']
        result = sut.system_test_from_config(config, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                  "docker",
                  "create",
                  "--network",
                  "local-foo-deploy-system-tests-abcd",
                  "--name",
                  "postgres-test",
                  "--rm",
                  "--env",
                  'FOO_DEPLOY_TEST_X="X"',
                  "--env",
                  'FOO_DEPLOY_TEST_Y="Y"',
                  "--env",
                  'POSTGRES_USER="tempuser"',
                  "--env",
                  'POSTGRES_PASSWORD="correct horse battery staple"',
                  "--publish",
                  "5432",
                  "postgres:13",
            ])], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_with_service_from_kubedev_locally(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                  "docker",
                  "create",
                  "--network",
                  "local-foo-deploy-system-tests-abcd",
                  "--name",
                  "postgres-test",
                  "--rm",
                  "--env",
                  'FOO_DEPLOY_TEST_X="X"',
                  "--env",
                  'FOO_DEPLOY_TEST_Y="Y"',
                  "--env",
                  'POSTGRES_USER="tempuser"',
                  "--env",
                  'POSTGRES_PASSWORD="correct horse battery staple"',
                  "--publish",
                  "5432",
                  "postgres:13",
            ])], [call['cmd'] for call in shellMock._calls])

        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                  "docker",
                  "create",
                  "--network",
                  "local-foo-deploy-system-tests-abcd",
                  "--name",
                  "foo-deploy-test",
                  "--rm",
                  "--env",
                  'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}"',
                  "--env",
                  'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                  "--env",
                  'FOO_DEPLOY_TEST_X="X"',
                  "--env",
                  'FOO_DEPLOY_TEST_Y="Y"',
                  "--env",
                  'FOO_SERVICE_DEPLOY_ENV1="fixed-value"',
                  "--publish",
                  "1234",
                  "foo-registry/foo-service-foo-deploy:none",
            ])], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_with_service_from_kubedev_in_ci(self):
        fileMock = FileMock()
        envMock = EnvMock()
        envMock.setenv('CI_COMMIT_SHORT_SHA', 'shacommit')
        envMock.setenv('CI_COMMIT_REF_NAME', 'branchname')
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                  "docker",
                  "create",
                  "--network",
                  "local-foo-deploy-system-tests-abcd",
                  "--name",
                  "foo-deploy-test",
                  "--rm",
                  "--env", # Note: FOO_SERVICE_DEPLOY_ENV1 is overridden in the systemTest spec, see below
                  'FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}"',
                  "--env",
                  'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                  "--env",
                  'FOO_DEPLOY_TEST_X="X"',
                  "--env",
                  'FOO_DEPLOY_TEST_Y="Y"',
                  "--env", # This overrides the value from the required-envs:
                  'FOO_SERVICE_DEPLOY_ENV1="fixed-value"',
                  "--publish",
                  "1234",
                  "foo-registry/foo-service-foo-deploy:shacommit_branchname",
            ])], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_cleans_up_services_after_run(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
          "docker",
          "rm",
          "--force",
          "docker_id_postgres"], [call['cmd'] for call in shellMock._calls])

        self.assertIn([
          "docker",
          "rm",
          "--force",
          "docker_id_foo_deploy"], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_cleans_up_network_after_run(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
          "docker",
          "network",
          "rm",
          "local-foo-deploy-system-tests-abcd"], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_creates_docker_config_in_ci(self):
        fileMock = FileMock()
        envMock = EnvMock()
        envMock.setenv('CI', 'yes')
        envMock.setenv('CI_COMMIT_SHORT_SHA', 'shacommit')
        envMock.setenv('CI_COMMIT_REF_NAME', 'branchname')
        envMock.setenv('DOCKER_AUTH_CONFIG', '{}')
        envMock.setenv('HOME', '/home/test')
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIsNotNone(fileMock.load_file('/home/test/.docker/config.json'))

    def test_systemtest_does_not_create_docker_config_if_not_in_ci(self):
        fileMock = FileMock()
        envMock = EnvMock()
        envMock.setenv('DOCKER_AUTH_CONFIG', '{}')
        envMock.setenv('HOME', '/home/test')
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testDeploymentConfig, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIsNone(fileMock.load_file('/home/test/.docker/config.json'))

    def test_systemtest_transforms_global_required_env_to_base64(self):
        fileMock = FileMock()
        envMock = EnvMock()
        envMock.setenv('DOCKER_AUTH_CONFIG', '{}')
        envMock.setenv('HOME', '/home/test')
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(configGlobalBase64Env, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                "docker",
                "run",
                "--rm",
                "--network",
                 "local-foo-deploy-system-tests-abcd",
                "--name", f"foo-deploy-system-tests-abcd",
                "--interactive",
                "--env",
                'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1_AS_BASE64}"',
                "local-foo-deploy-system-tests-abcd"
            ])
        ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_transforms_deployment_required_env_to_base64(self):
        fileMock = FileMock()
        envMock = EnvMock()
        envMock.setenv('DOCKER_AUTH_CONFIG', '{}')
        envMock.setenv('HOME', '/home/test')
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_foo_deploy'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(configDeploymentBase64Env, 'foo-deploy', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        expectedCall = [
            "/bin/sh",
            "-c",
            " ".join([
                "docker",
                "run",
                "--rm",
                "--network",
                 "local-foo-deploy-system-tests-abcd",
                "--name", f"foo-deploy-system-tests-abcd",
                "--interactive",
                "--env",
                'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1_AS_BASE64}"',
                "local-foo-deploy-system-tests-abcd"
            ])
        ]
        self.assertIn(expectedCall, [call['cmd'] for call in shellMock._calls])
        dockerRunCallEnvs = [call['env'] for call in shellMock._calls if call['cmd'] == expectedCall][0]
        self.assertIn('FOO_SERVICE_GLOBAL_ENV1_AS_BASE64', dockerRunCallEnvs)

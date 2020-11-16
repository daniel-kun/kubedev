import copy
import unittest

import yaml
from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock, SleepMock,
                        TagGeneratorMock, testCronJobConfig)


class KubeDevSystemTestCronJobTests(unittest.TestCase):
    def test_systemtest_spins_up_kind_cluster(self):
        # ARRANGE
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock()
        tagMock = TagGeneratorMock(["asdf"])
        sleepMock = SleepMock()

        # ACT
        sut = Kubedev()
        result = sut.system_test_from_config(
            testCronJobConfig,
            "foo-job",
            file_accessor=fileMock,
            env_accessor=envMock,
            shell_executor=shellMock,
            tag_generator=tagMock,
            sleeper=sleepMock)

        # ASSERT
        self.assertTrue(result)

        calls = [call['cmd'] for call in shellMock._calls]
        self.assertIn([
            "kind",
            "create",
            "cluster",
            "--kubeconfig",
            ".kubedev/kind_config_foo-service-asdf",
            "--wait",
            "10m",
            "--name",
            "kind-foo-service-asdf"
        ], calls)

    def test_systemtest_deletes_kind_cluster(self):
        # ARRANGE
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock()
        tagMock = TagGeneratorMock(["asdf"])
        sleepMock = SleepMock()

        # ACT
        sut = Kubedev()
        result = sut.system_test_from_config(
            testCronJobConfig,
            "foo-job",
            file_accessor=fileMock,
            env_accessor=envMock,
            shell_executor=shellMock,
            tag_generator=tagMock,
            sleeper=sleepMock)

        # ASSERT
        self.assertTrue(result)

        calls = [call['cmd'] for call in shellMock._calls]
        self.assertIn([
            "kind",
            "delete",
            "cluster",
            "--name",
            "kind-foo-service-asdf"
        ], calls)

    def test_systemtest_builds_test_container(self):
        # ARRANGE
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock()
        tagMock = TagGeneratorMock(["asdf"])
        sleepMock = SleepMock()

        # ACT
        sut = Kubedev()
        result = sut.system_test_from_config(
            testCronJobConfig,
            "foo-job",
            file_accessor=fileMock,
            env_accessor=envMock,
            shell_executor=shellMock,
            tag_generator=tagMock,
            sleeper=sleepMock)

        # ASSERT
        self.assertTrue(result)

        calls = [call['cmd'] for call in shellMock._calls]
        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                "docker",
                "build",
                "-t",
                "local-foo-job-system-tests-asdf",
                "--build-args",
                'FOO_JOB_BUILD_ARG="asdf"',
                "./systemTests/foo-job/"
            ])
        ], calls)

    def test_systemtest_runs_test_container_with_kubeconf(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres', 'docker_id_'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        result = sut.system_test_from_config(testCronJobConfig, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)
        # Check for running of the test container:
        self.assertIn([
              "/bin/sh",
              "-c",
              " ".join([
                  "docker",
                  "run",
                  "--rm",
                  "--network", 'local-foo-job-system-tests-abcd',
                  "--name", "foo-job-system-tests-abcd",
                  "--interactive",
                  "--volume",
                  "/kubedev/systemtests/.kubedev/kind_config_foo-service-abcd:/tmp/kube_config",
                  "--env",
                  "KUBECONFIG=/tmp/kube_config",
                  "--env",
                  'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                  "--env",
                  'FOO_SERVICE_JOB_ENV1="${FOO_SERVICE_JOB_ENV1}"',
                  "--env",
                  'FOO_SERVICE_JOB_ENV2="${FOO_SERVICE_JOB_ENV2}"',
                  "--env",
                  'POSTGRES_USER="testadmin"',
                  "local-foo-job-system-tests-abcd"
                  ])
        ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_with_service_from_registry_with_variables(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testCronJobConfig)
        result = sut.system_test_from_config(config, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                  "docker",
                  "create",
                  "--network",
                  "local-foo-job-system-tests-abcd",
                  "--name",
                  "postgres-test",
                  "--rm",
                  "--env",
                  'POSTGRES_USER="testadmin"',
                  "--env",
                  'POSTGRES_PASSWORD="correct horse battery staple"',
                  "--publish",
                  "5432",
                  "postgres:13",
            ])], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_changes_kubeconf_servers_to_kind_control_plane(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['docker_id_postgres'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        fileMock.save_file('.kubedev/kind_config_foo-service-abcd', '''apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: Foo
    server: https://127.0.0.1:58436
  name: kind-kind-foo-service-abcd
contexts:
- context:
    cluster: kind-kind-foo-service-abcd
    user: kind-kind-foo-service-abcd
  name: kind-kind-foo-service-abcd
current-context: kind-kind-foo-service-abcd
kind: Config
preferences: {}
users:
- name: kind-kind-foo-service-abcd
  user:
    client-certificate-data: Foo
    client-key-data: Foo
''', overwrite=True)

        sut = Kubedev()
        config = copy.deepcopy(testCronJobConfig)
        result = sut.system_test_from_config(config, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        kubeConfFile = fileMock.load_file('.kubedev/kind_config_foo-service-abcd')
        self.assertIsNotNone(kubeConfFile)
        kubeConf = yaml.safe_load(kubeConfFile)
        for cluster in kubeConf['clusters']:
            self.assertEqual(f'https://kind-foo-service-abcd-control-plane:6443', cluster['cluster']['server'])

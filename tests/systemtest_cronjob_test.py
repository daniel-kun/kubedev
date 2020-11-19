import copy
import unittest

import yaml
from kubedev import Kubedev
from kubedev.utils import KubernetesTools
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

    def test_systemtest_creates_docker_secret(self):
        # ARRANGE
        fileMock = FileMock()
        envMock = EnvMock()
        envMock.setenv('DOCKER_AUTH_CONFIG', '{"test": true"}')
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
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
        self.assertEquals(result, 0)

        calls = [call['cmd'] for call in shellMock._calls]
        self.assertIn([
            "/bin/sh",
            "-c",
            " ".join([
                "docker",
                "run",
                "-i",
                "--rm",
                '--network',
                'local-foo-job-system-tests-asdf',
                '--volume',
                "/kubedev/systemtests/.kubedev/kind_config_foo-service-asdf:/tmp/kube_config",
                "--env",
                "DOCKER_AUTH_CONFIG",
                "bitnami/kubectl:1.18",
                "--kubeconfig",
                "/tmp/kube_config",
                "create",
                "secret",
                "generic",
                "foo-creds",
                "--type",
                "kubernetes.io/dockerconfigjson",
                '--from-literal=.dockerconfigjson="${DOCKER_AUTH_CONFIG}"'
            ])], calls)

    def test_systemtest_builds_apps(self):
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
                'foo-registry/foo-service-foo-job:asdf',
                '--build-arg',
                'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
                '--build-arg',
                'FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}"',
                '--build-arg',
                'FOO_SERVICE_JOB_ENV1="${FOO_SERVICE_JOB_ENV1}"',
                '--build-arg',
                'FOO_SERVICE_JOB_ENV2="${FOO_SERVICE_JOB_ENV2}"',
                '--build-arg',
                'FOO_SERVICE_JOB_ENV3="${FOO_SERVICE_JOB_ENV3}"',
                './foo-job/'
            ])
        ], calls)

    def test_systemtest_runs_test_container_with_kubeconf(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
        tagMock = TagGeneratorMock(['abcd', 'apikey'])
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
                  "--env",
                  'KUBEDEV_SYSTEMTEST_DAEMON_APIKEY="apikey"',
                  '--env',
                  'KUBEDEV_SYSTEMTEST_DAEMON_ENDPOINT="http://kubedev-run-cronjob-api:5000/execute"',
                  "local-foo-job-system-tests-abcd"
                  ])
        ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_run_with_service_from_registry_with_variables(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
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
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
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

    def test_systemtest_inits_helm_and_deploys_to_kind_cluster(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testCronJobConfig)
        result = sut.system_test_from_config(config, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        expectedKubeCtlApply = [
            'docker',
            'run',
            '-i',
            '--rm',
            '--network',
            'local-foo-job-system-tests-abcd',
            '--volume',
            '/kubedev/systemtests/.kubedev/kind_config_foo-service-abcd:/tmp/kube_config',
            'bitnami/kubectl:1.18',
            '--kubeconfig',
            '/tmp/kube_config',
            'apply',
            '-f',
            '-']
        self.assertIn(expectedKubeCtlApply, [call['cmd'] for call in shellMock._calls])
        kubeCtlApplyCal = [call for call in shellMock._calls if call['cmd'] == expectedKubeCtlApply][0]
        self.assertEqual(KubernetesTools.get_tiller_rbac_setup(), kubeCtlApplyCal['pipedInput'])

        self.assertIn([
            'docker',
            'run',
            '-i',
            '--rm',
            '--network',
            'local-foo-job-system-tests-abcd',
            '--volume',
            '/kubedev/systemtests/.kubedev/kind_config_foo-service-abcd:/tmp/kube_config',
            'alpine/helm:2.16.9',
            '--kubeconfig',
            '/tmp/kube_config',
            'init',
            '--service-account',
            'tiller'], [call['cmd'] for call in shellMock._calls])

        self.assertIn([
            'docker',
            'run',
            '-i',
            '--rm',
            '--network',
            'local-foo-job-system-tests-abcd',
            '--volume',
            '/kubedev/systemtests/.kubedev/kind_config_foo-service-abcd:/tmp/kube_config',
            '--volume',
            '/kubedev/systemtests/helm-chart/:/app/helm-chart/',
            'alpine/helm:2.16.9',
            'upgrade',
            'local-foo-job-system-tests-abcd',
            '/app/helm-chart/',
            '--install',
            '--wait',
            '--kubeconfig',
            '/tmp/kube_config',
            '--set', 'KUBEDEV_TAG=abcd',
            '--set', 'FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"',
            '--set', 'FOO_SERVICE_JOB_ENV1="${FOO_SERVICE_JOB_ENV1}"',
            '--set', 'FOO_SERVICE_JOB_ENV2="${FOO_SERVICE_JOB_ENV2}"'
            ], [call['cmd'] for call in shellMock._calls])

    def test_systemtest_checks_for_tiller_to_become_ready(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['x', 'y',  '{"status": {}}','{"status": {"availableReplicas": 0}}', '{"status": {"availableReplicas": 1}}'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testCronJobConfig)
        result = sut.system_test_from_config(config, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        expectedCall = [
            'docker',
            'run',
            '-i',
            '--rm',
            '--network',
            'local-foo-job-system-tests-abcd',
            '--volume',
            '/kubedev/systemtests/.kubedev/kind_config_foo-service-abcd:/tmp/kube_config',
            'bitnami/kubectl:1.18',
            '--kubeconfig',
            '/tmp/kube_config',
            '--namespace',
            'kube-system',
            'get',
            'deployments',
            'tiller-deploy',
            '-o',
            'json'
            ]

        self.assertIn(expectedCall, [call['cmd'] for call in shellMock._calls])
        checkTillerCommands = [call['cmd'] for call in shellMock._calls if call['cmd'] == expectedCall]
        self.assertEqual(3, len(checkTillerCommands))


    def test_systemtest_succeeds_without_env_vars(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testCronJobConfig)
        del config['required-envs']
        del config['cronjobs']['foo-job']['required-envs']
        result = sut.system_test_from_config(config, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

    def test_systemtest_deletes_docker_network(self):
        fileMock = FileMock()
        envMock = EnvMock()
        shellMock = ShellExecutorMock(cmd_output=['x', 'y', '{"status": {"availableReplicas": 1}}'])
        tagMock = TagGeneratorMock(['abcd'])
        sleeper = SleepMock()

        sut = Kubedev()
        config = copy.deepcopy(testCronJobConfig)
        result = sut.system_test_from_config(config, 'foo-job', fileMock, envMock, shellMock, tagMock, sleeper)

        self.assertEqual(result, 0)

        self.assertIn([
            'docker',
            'network',
            'rm',
            'local-foo-job-system-tests-abcd'
        ], [call['cmd'] for call in shellMock._calls])

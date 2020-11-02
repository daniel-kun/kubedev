import copy
import unittest

from kubedev import Kubedev
from test_utils import (DownloadMock, EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig)


class KubeDevAuditTests(unittest.TestCase):
    def test_audit_helm_chart(self):
        # ARRANGE
        shell = ShellExecutorMock(cmd_output=["asdf"])
        downloader = DownloadMock(True, "")
        fileMock = FileMock()
        env = EnvMock()
        env.setenv('HOME', '/home/kubedev')

        # ACT
        kubedev = Kubedev()
        config = copy.deepcopy(testDeploymentConfig)
        del config['securityChecks'] # Run polaris checks with default configuration
        kubedev.audit_from_config(config, downloader, fileMock, shell, env)


        # ASSERT
        actual_command = shell.calls()[1]["cmd"]
        expected_command = [
            "polaris",
            "audit",
            "--set-exit-code-on-danger",
            "--format",
            "yaml",
            "--audit-path",
            "-"
        ]

        self.assertListEqual(expected_command, actual_command)

    def test_use_config_file(self):
        # ARRANGE
        config = copy.deepcopy(testDeploymentConfig)
        del config['securityChecks']['polaris']['configDownload'] # Run polaris checks with custom file

        shell = ShellExecutorMock(cmd_output=["asdf"])
        downloader = DownloadMock(True, "")
        fileMock = FileMock()
        fileMock.save_file("polaris-config-cli-v3.yaml", 'asdf', True)
        env = EnvMock()
        env.setenv('HOME', '/home/kubedev')
        env.setenv('POLARIS_CONFIG_VERSION_LOCAL', '3')

        # ACT
        kubedev = Kubedev()
        kubedev.audit_from_config(config, downloader, fileMock, shell, env)


        # ASSERT
        actual_command = shell.calls()[1]["cmd"]
        expected_command = [
            "polaris",
            "audit",
            "--config",
            "polaris-config-cli-v3.yaml",
            "--set-exit-code-on-danger",
            "--format",
            "yaml",
            "--audit-path",
            "-"
        ]

        self.assertListEqual(expected_command, actual_command)
        self.assertListEqual([], downloader._calls)

    def test_skip_confg_file_if_not_exists(self):
        # ARRANGE
        shell = ShellExecutorMock(cmd_output=["asdf"])
        downloader = DownloadMock(True, "")
        fileMock = FileMock()
        env = EnvMock()
        env.setenv('HOME', '/home/kubedev')
        env.setenv('POLARIS_CONFIG_VERSION_LOCAL', '3')

        # ACT
        kubedev = Kubedev()
        config = copy.deepcopy(testDeploymentConfig)
        del config['securityChecks']['polaris']['configDownload'] # Run polaris checks without custom, local file
        kubedev.audit_from_config(config, downloader, fileMock, shell, env)


        # ASSERT
        actual_command = shell.calls()[1]["cmd"]
        expected_command = [
            "polaris",
            "audit",
            "--set-exit-code-on-danger",
            "--format",
            "yaml",
            "--audit-path",
            "-",
        ]

        self.assertEqual(len(expected_command), len(actual_command))
        self.assertListEqual(expected_command, actual_command)

    def test_download_and_expand_env_vars(self):
        # ARRANGE
        shell = ShellExecutorMock(cmd_output=["asdf"])
        downloader = DownloadMock(True, "")
        fileMock = FileMock()
        env = EnvMock()
        env.setenv('HOME', '/home/kubedev')

        env.setenv('POLARIS_CONFIG_VERSION_LOCAL', '3')
        env.setenv('POLARIS_CONFIG_VERSION', '4')
        env.setenv('YOUR_BEARER_TOKEN', 'DEADBEEF')

        # ACT
        kubedev = Kubedev()
        kubedev.audit_from_config(testDeploymentConfig, downloader, fileMock, shell, env)


        # ASSERT
        actual_command = shell.calls()[1]["cmd"]
        expected_command = [
            "polaris",
            "audit",
            "--config",
            "polaris-config-cli-v3.yaml",
            "--set-exit-code-on-danger",
            "--format",
            "yaml",
            "--audit-path",
            "-",
        ]

        self.assertListEqual(expected_command, actual_command)
        self.assertListEqual([["https://url-to-your/polaris-config-v4.yaml", {"Authentication": "Bearer DEADBEEF"}, "polaris-config-cli-v3.yaml"]], downloader._calls)

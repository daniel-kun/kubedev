import unittest

import test_utils
from kubedev import Kubedev


class KubeDevAuditTests(unittest.TestCase):
    def test_audit_helm_chart(self):
        print("Testing kubedev audit")
        # ARRANGE
        shell = test_utils.ShellExecutorMock()
        env = test_utils.EnvMock()
        env.setenv('HOME', '/home/kubedev')

        # ACT
        kubedev = Kubedev()
        kubedev.audit_from_config(test_utils.testDeploymentConfig, shell, env)
        actual_command = list()
        for cmd in shell.calls()[0]["cmd"]:
            if cmd:
                actual_command.append(cmd) 
        expected_command = [
            "polaris",
            "audit",
            "--audit-path",
            "-",
            "--set-exit-code-on-danger",
            "--format",
            "yaml"
        ]
        self.assertListEqual(expected_command, actual_command)

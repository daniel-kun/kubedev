import unittest

import yaml

from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig)


class KubeDevTemplateTests(unittest.TestCase):

  def test_template_single_deployment(self):
    # ARRANGE
    shell = ShellExecutorMock()
    env = EnvMock()
    env.setenv('HOME', '/home/kubedev')
    env.setenv('SHELL', '/bin/sh')
    env.setenv('KUBEDEV_KUBECONFIG', 'default')
    env.setenv('KUBEDEV_KUBECONTEXT', 'kubedev-ctx')

    # ACT
    sut = Kubedev('./templates/')
    sut.template_from_config(testDeploymentConfig, shell, env)

    # ASSERT
    shellCalls = shell.calls()
    print('==============')
    print(shellCalls[0]['cmd'])
    print('==============')
    self.assertEqual(1, len(shellCalls))
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'helm template ./helm-chart/ --name foo-service --wait --kubeconfig ' +
        '/home/kubedev/.kube/config --kube-context kubedev-ctx ' +
        '--set KUBEDEV_TAG="abcd_master" ' +
        '--set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" --set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"'
    ], shellCalls[0]['cmd'])

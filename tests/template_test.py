import unittest

import yaml
from kubedev import Kubedev
from test_utils import (EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig, testMultiDeploymentsConfig)


class KubeDevTemplateTests(unittest.TestCase):

  def test_template_single_deployment_non_ci(self):
    # ARRANGE
    shell = ShellExecutorMock()
    env = EnvMock()
    env.setenv('HOME', '/home/kubedev')

    files = FileMock()

    # ACT
    sut = Kubedev()
    sut.template_from_config(testDeploymentConfig, shell, env, files)

    # ASSERT
    shellCalls = shell.calls()
    self.assertEqual(1, len(shellCalls))
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'helm template ./helm-chart/ ' +
        '--set KUBEDEV_TAG="none" ' +
        '--set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" --set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"'
    ], shellCalls[0]['cmd'])

  def test_template_multiple_deployments_in_ci(self):
    # ARRANGE
    shell = ShellExecutorMock()
    env = EnvMock()
    env.setenv('HOME', '/home/kubedev')
    env.setenv('CI_COMMIT_SHORT_SHA', 'shortsha')
    env.setenv('CI_COMMIT_REF_NAME', 'branchname')

    files = FileMock()

    # ACT
    sut = Kubedev()
    sut.template_from_config(testMultiDeploymentsConfig, shell, env, files)

    # ASSERT
    shellCalls = shell.calls()
    self.assertEqual(1, len(shellCalls))
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'helm template ./helm-chart/ ' +
        '--set KUBEDEV_TAG="shortsha_branchname" ' +
        '--set BAR_SERVICE_DEPLOY_ENV1="${BAR_SERVICE_DEPLOY_ENV1}" --set BAR_SERVICE_DEPLOY_ENV2="${BAR_SERVICE_DEPLOY_ENV2}" ' +
        '--set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
        '--set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" --set FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}"'
    ], shellCalls[0]['cmd'])

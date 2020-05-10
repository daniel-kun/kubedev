import unittest

import yaml

from kubedev import Kubedev
from kubedev.utils import kubeconfig_temp_path
from test_utils import (EnvMock, FileMock, ShellExecutorMock,
                        testDeploymentConfig, testMultiDeploymentsConfig)


class KubeDevTemplateTests(unittest.TestCase):

  def test_template_single_deployment_non_ci(self):
    # ARRANGE
    shell = ShellExecutorMock()
    env = EnvMock()
    env.setenv('HOME', '/home/kubedev')
    env.setenv('SHELL', '/bin/sh')
    env.setenv('KUBEDEV_KUBECONFIG', 'default')
    env.setenv('KUBEDEV_KUBECONTEXT', 'kubedev-ctx')

    files = FileMock()

    # ACT
    sut = Kubedev('./templates/')
    sut.template_from_config(testDeploymentConfig, shell, env, files)

    # ASSERT
    shellCalls = shell.calls()
    self.assertEqual(1, len(shellCalls))
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'helm template ./helm-chart/ --name foo-service --kubeconfig ' +
        '/home/kubedev/.kube/config --kube-context kubedev-ctx ' +
        '--set KUBEDEV_TAG="none" ' +
        '--set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" --set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}"'
    ], shellCalls[0]['cmd'])

  def test_template_multiple_deployments_in_ci(self):
    # ARRANGE
    shell = ShellExecutorMock()
    env = EnvMock()
    env.setenv('HOME', '/home/kubedev')
    env.setenv('SHELL', '/bin/sh')
    kubeConfigContent = '''
lkasjfjklsdflkj:
  foo: aksldajsf
  bar: lskdjfsd
'''
    env.setenv('KUBEDEV_KUBECONFIG', kubeConfigContent)
    env.setenv('KUBEDEV_KUBECONTEXT', 'kubedev-ctx')
    env.setenv('CI_COMMIT_SHORT_SHA', 'shortsha')
    env.setenv('CI_COMMIT_REF_NAME', 'branchname')

    files = FileMock()

    # ACT
    sut = Kubedev('./templates/')
    sut.template_from_config(testMultiDeploymentsConfig, shell, env, files)

    # ASSERT
    shellCalls = shell.calls()
    self.assertEqual(1, len(shellCalls))
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'helm template ./helm-chart/ --name foo-service --kubeconfig ' +
        f'{kubeconfig_temp_path} --kube-context kubedev-ctx ' +
        '--set KUBEDEV_TAG="shortsha_branchname" ' +
        '--set BAR_SERVICE_DEPLOY_ENV1="${BAR_SERVICE_DEPLOY_ENV1}" --set BAR_SERVICE_DEPLOY_ENV2="${BAR_SERVICE_DEPLOY_ENV2}" ' +
        '--set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
        '--set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" --set FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}"'
    ], shellCalls[0]['cmd'])
    kubeConfig = files.load_file(kubeconfig_temp_path)
    self.assertIsNotNone(kubeConfig)
    self.assertEqual(kubeConfig, kubeConfigContent)

import copy
import unittest
from base64 import b64encode

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

  def test_template_with_b64_transformed_variables(self):
    # ARRANGE
    shell = ShellExecutorMock()
    env = EnvMock()
    binaryValue = "🙂😎😣😪\r\n\t {} $''\"❤"
    env.setenv('FOO_DEPLOY_BINARY_VALUE', binaryValue)
    env.setenv('FOO_DEPLOY_GLOBAL_BINARY_VALUE', binaryValue + binaryValue)
    files = FileMock()

    # ACT
    sut = Kubedev()
    config = copy.deepcopy(testMultiDeploymentsConfig)
    config['deployments']['foo-deploy']['required-envs']['FOO_DEPLOY_BINARY_VALUE'] = {
      "documentation": "A value that will be auto-base64 before passing it to helm",
      "container": True,
      "build": False,
      "transform": "base64"
    }
    config['required-envs']['FOO_DEPLOY_GLOBAL_BINARY_VALUE'] = {
      "documentation": "A value that will be auto-base64 before passing it to helm",
      "container": True,
      "build": False,
      "transform": "base64"
    }
    sut.template_from_config(config, shell, env, files)

    # ASSERT
    shellCalls = shell.calls()
    self.assertEqual(1, len(shellCalls))
    helmTemplateCall = shellCalls[0]
    helmTemplateEnv = helmTemplateCall['env']
    helmTemplateCommand = helmTemplateCall['cmd']
    self.assertListEqual([
        '/bin/sh',
        '-c',
        'helm template ./helm-chart/ ' +
        '--set KUBEDEV_TAG="none" ' +
        '--set BAR_SERVICE_DEPLOY_ENV1="${BAR_SERVICE_DEPLOY_ENV1}" --set BAR_SERVICE_DEPLOY_ENV2="${BAR_SERVICE_DEPLOY_ENV2}" ' +
        '--set FOO_DEPLOY_BINARY_VALUE="${FOO_DEPLOY_BINARY_VALUE_AS_BASE64}" --set FOO_DEPLOY_GLOBAL_BINARY_VALUE="${FOO_DEPLOY_GLOBAL_BINARY_VALUE_AS_BASE64}" ' +
        '--set FOO_SERVICE_DEPLOY_ENV1="${FOO_SERVICE_DEPLOY_ENV1}" --set FOO_SERVICE_DEPLOY_ENV2="${FOO_SERVICE_DEPLOY_ENV2}" ' +
        '--set FOO_SERVICE_GLOBAL_ENV1="${FOO_SERVICE_GLOBAL_ENV1}" --set FOO_SERVICE_GLOBAL_ENV2="${FOO_SERVICE_GLOBAL_ENV2}"' +
        ''
    ], helmTemplateCommand)
    self.assertIn('FOO_DEPLOY_BINARY_VALUE_AS_BASE64', helmTemplateEnv)
    self.assertIn('FOO_DEPLOY_GLOBAL_BINARY_VALUE_AS_BASE64', helmTemplateEnv)
    self.assertEqual(helmTemplateEnv['FOO_DEPLOY_BINARY_VALUE_AS_BASE64'], b64encode(binaryValue.encode('utf-8')))
    self.assertEqual(helmTemplateEnv['FOO_DEPLOY_GLOBAL_BINARY_VALUE_AS_BASE64'], b64encode((binaryValue + binaryValue).encode('utf-8')))

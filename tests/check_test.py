import json
import unittest

import yaml
from kubedev import Kubedev, main_impl
from test_utils import (EnvMock, FileMock, OutputMock, ShellExecutorMock,
                        testCronJobConfig, testDeploymentConfig,
                        testMultiDeploymentsConfig)


def _set_all_envs(env):
  env.setenv('FOO_SERVICE_GLOBAL_ENV1', 'g1')
  env.setenv('FOO_SERVICE_GLOBAL_ENV2', 'g2')
  env.setenv('FOO_SERVICE_DEPLOY_ENV1', 'd1')
  env.setenv('FOO_SERVICE_DEPLOY_ENV2', 'd2')
  env.setenv('BAR_SERVICE_DEPLOY_ENV1', 'b1')
  env.setenv('BAR_SERVICE_DEPLOY_ENV2', 'b2')


class KubeDevCheckTests(unittest.TestCase):

  def test_check_env_multi_deployment_all_set(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()

    fileMock = FileMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testMultiDeploymentsConfig, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)

    self.assertTrue(result)
    messages = outputMock.messages()
    self.assertEqual(0, len(messages))

  def test_check_env_multi_deployment_one_missing(self):
    envMock = EnvMock()
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV1', 'g1')
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV2', 'g2')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV1', 'd1')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV2', 'd2')
    envMock.setenv('BAR_SERVICE_DEPLOY_ENV1', 'b1')
    outputMock = OutputMock()
    fileMock = FileMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testMultiDeploymentsConfig, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    self.assertEqual(1, len(messages))
    self.assertIn('not defined', messages[0]['message'].lower())

  def test_check_env_multi_deployment_multiple_missing(self):
    envMock = EnvMock()
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV1', 'g1')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV2', 'd2')
    envMock.setenv('BAR_SERVICE_DEPLOY_ENV1', 'b1')
    outputMock = OutputMock()
    fileMock = FileMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testMultiDeploymentsConfig, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    print(messages)
    self.assertEqual(3, len(messages))
    self.assertIn('not defined', messages[0]['message'].lower())

  def test_check_env_tests_vars_with_build_or_container_set_to_false(self):
    envMock = EnvMock()
    outputMock = OutputMock()
    fileMock = FileMock()

    sut = Kubedev()
    result = sut.check_from_config(
        {
            "name": "test",
            "imagePullSecrets": "foobar",
            "imageRegistry": "foobar",
            "required-envs": {
                "XYZ": {
                    "build": True,
                    "container": False
                }
            },
            "deployments": {
                "test": {
                    "required-envs": {
                        "ABC": {
                            "build": False,
                            "container": True
                        }
                    }
                }
            }
        }, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    print(messages)
    self.assertEqual(2, len(messages))
    self.assertIn('not defined', messages[0]['message'].lower())

  def test_check_image_registry_missing(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()
    fileMock = FileMock()

    config = testMultiDeploymentsConfig.copy()
    del config['imageRegistry']

    sut = Kubedev()
    result = sut.check_from_config(
        config, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    # Verify that the error message contains the string 'imageRegistry'
    self.assertIn('imageRegistry', messages[0]["message"])

  def test_check_image_pullsecrets_missing(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()
    fileMock = FileMock()

    config = testMultiDeploymentsConfig.copy()
    del config['imagePullSecrets']

    sut = Kubedev()
    result = sut.check_from_config(
        config, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    # Verify that the error message contains the string 'imagePullSecrets'
    self.assertIn('imagePullSecrets', messages[0]["message"])

  def test_check_name_missing(self):
    envMock = EnvMock()
    _set_all_envs(envMock)

    outputMock = OutputMock()
    fileMock = FileMock()

    config = testMultiDeploymentsConfig.copy()
    del config['name']

    sut = Kubedev()
    result = sut.check_from_config(
        config, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    self.assertFalse(result)
    messages = outputMock.messages()
    # Verify that the error message contains the string 'name'
    self.assertIn('name', messages[0]["message"])

  def test_check_cmdline_build_all_set(self):
    envMock = EnvMock()
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV2', 'X')
    envMock.setenv('FOO_SERVICE_DEPLOY_ENV1', 'X')
    envMock.setenv('BAR_SERVICE_DEPLOY_ENV1', 'X')
    outputMock = OutputMock()
    fileMock = FileMock()
    # Test that env-vars with "build" not set or "build" set to false are not checked:
    fileMock.save_file('kubedev.json', json.dumps(
        {
            "name": "foo-service",
            "required-envs": {
                "FOO_SERVICE_GLOBAL_ENV1": {
                    "documentation": "Test env var #1 (global)",
                    "build": False
                },
                "FOO_SERVICE_GLOBAL_ENV2": {
                    "documentation": "Test env var #2 (global)"
                },
            },
            "deployments": {
                "foo-deploy": {
                    "required-envs": {
                        "FOO_SERVICE_DEPLOY_ENV1": {
                            "documentation": "Test env var #1, service 'foo-deploy'"
                        },
                        "FOO_SERVICE_DEPLOY_ENV2": {
                            "documentation": "Test env var #2, service 'foo-deploy'",
                            "build": False
                        }
                    }
                },
                "bar-deploy": {
                    "required-envs": {
                        "BAR_SERVICE_DEPLOY_ENV1": {
                            "documentation": "Test env var #1, service 'bar-deploy'",
                            "container": False
                        },
                        "BAR_SERVICE_DEPLOY_ENV2": {
                            "documentation": "Test env var #2, service 'bar-deploy'",
                            "build": False
                        }
                    }
                }
            }
        }), True)

    result = main_impl(['/somewhere/kubedev', 'check', 'build'],
                       env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    messages = outputMock.messages()
    if result != 0:
      self.assertTrue(False, f"Did not expect these messages: {messages}")
    self.assertEqual(0, result)

  def test_check_cmdline_build_some_missing(self):
    envMock = EnvMock()
    envMock.setenv('FOO_SERVICE_GLOBAL_ENV2', 'X')
    envMock.setenv('BAR_SERVICE_DEPLOY_ENV1', 'X')
    outputMock = OutputMock()
    fileMock = FileMock()
    # Test that env-vars with "build" not set or "build" set to false are not checked:
    fileMock.save_file('kubedev.json', json.dumps(
        {
            "name": "foo-service",
            "required-envs": {
                "FOO_SERVICE_GLOBAL_ENV1": {
                    "documentation": "Test env var #1 (global)",
                    "build": False
                },
                "FOO_SERVICE_GLOBAL_ENV2": {
                    "documentation": "Test env var #2 (global)"
                },
            },
            "deployments": {
                "foo-deploy": {
                    "required-envs": {
                        "FOO_SERVICE_DEPLOY_ENV1": {
                            "documentation": "Test env var #1, service 'foo-deploy'"
                        },
                        "FOO_SERVICE_DEPLOY_ENV2": {
                            "documentation": "Test env var #2, service 'foo-deploy'",
                            "build": False
                        }
                    }
                },
                "bar-deploy": {
                    "required-envs": {
                        "BAR_SERVICE_DEPLOY_ENV1": {
                            "documentation": "Test env var #1, service 'bar-deploy'",
                            "container": False
                        },
                        "BAR_SERVICE_DEPLOY_ENV2": {
                            "documentation": "Test env var #2, service 'bar-deploy'",
                            "build": False
                        }
                    }
                }
            }
        }), True)

    result = main_impl(['/somewhere/kubedev', 'check', 'build'],
                       env_accessor=envMock, printer=outputMock, file_accessor=fileMock)
    messages = outputMock.messages()
    self.assertNotEqual(0, result)
    self.assertEqual(1, len(messages))
    self.assertIn('FOO_SERVICE_DEPLOY_ENV1', messages[0]['message'])

  def test_check_cronjob_envs(self):
    envMock = EnvMock()
    outputMock = OutputMock()
    fileMock = FileMock()

    sut = Kubedev()
    result = sut.check_from_config(
        testCronJobConfig, [], env_accessor=envMock, printer=outputMock, file_accessor=fileMock)

    self.assertFalse(result)
    messages = outputMock.messages()
    self.assertEqual(5, len(messages))

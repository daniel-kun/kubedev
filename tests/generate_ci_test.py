import unittest

import yaml
from kubedev import Kubedev
from test_utils import EnvMock, FileMock, TemplateMock, testDeploymentConfig


class KubeDevGenerateCITests(unittest.TestCase):

  def test_ci_config_exists(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()
    envMock.setenv('CI_COMMIT_SHORT_SHA', 'asdf')
    envMock.setenv('CI_COMMIT_REF_NAME', '_branch')

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    ciYaml = fileMock.load_file('.gitlab-ci.yml')
    self.assertIsNotNone(ciYaml)

  def test_ci_stages_exist(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()
    envMock.setenv('CI_COMMIT_SHORT_SHA', 'asdf')
    envMock.setenv('CI_COMMIT_REF_NAME', '_branch')

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    ciYaml = fileMock.load_file('.gitlab-ci.yml')
    self.assertIsNotNone(ciYaml)
    ci = yaml.safe_load(ciYaml)
    self.assertIn('stages', ci)
    self.assertIn('build-push', ci['stages'])
    self.assertIn('deploy', ci['stages'])

  def test_ci_build_push_foo_deploy(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()
    envMock.setenv('CI_COMMIT_SHORT_SHA', 'asdf')
    envMock.setenv('CI_COMMIT_REF_NAME', '_branch')

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    ciYaml = fileMock.load_file('.gitlab-ci.yml')
    self.assertIsNotNone(ciYaml)
    ci = yaml.safe_load(ciYaml)
    self.assertIn('build-push-foo-deploy', ci)
    job = ci['build-push-foo-deploy']
    self.assertEqual('build-push', job['stage'])
    self.assertIn('image', job)
    self.assertIn('script', job)
    self.assertIn('variables', job)
    self.assertIn('KUBEDEV_TAG', job['variables'])
    self.assertEqual(
        '${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}', job['variables']['KUBEDEV_TAG'])

  def test_ci_build_push_foo_deploy_script(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()
    envMock.setenv('CI_COMMIT_SHORT_SHA', 'asdf')
    envMock.setenv('CI_COMMIT_REF_NAME', '_branch')

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    ciYaml = fileMock.load_file('.gitlab-ci.yml')
    self.assertIsNotNone(ciYaml)
    ci = yaml.safe_load(ciYaml)
    self.assertIn('build-push-foo-deploy', ci)
    job = ci['build-push-foo-deploy']
    self.assertIn('script', job)
    self.assertListEqual(
        ['kubedev check',
         'kubedev build foo-deploy',
         'kubedev push foo-deploy'],
        job['script'])

  def test_ci_deploy(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()
    envMock.setenv('CI_COMMIT_SHORT_SHA', 'asdf')
    envMock.setenv('CI_COMMIT_REF_NAME', '_branch')

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    ciYaml = fileMock.load_file('.gitlab-ci.yml')
    self.assertIsNotNone(ciYaml)
    ci = yaml.safe_load(ciYaml)
    self.assertIn('deploy', ci)
    job = ci['deploy']
    self.assertEqual('deploy', job['stage'])
    self.assertIn('image', job)
    self.assertIn('script', job)
    self.assertListEqual(
        ['kubedev check',
         'kubedev deploy --version ${CI_PIPELINE_IID}'],
        job['script'])
    self.assertIn('variables', job)
    self.assertIn('KUBEDEV_TAG', job['variables'])
    self.assertEqual(
        '${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}', job['variables']['KUBEDEV_TAG'])

  def test_ci_uses_equal_kubedev_version(self):
    self.skipTest('Not yet implemented: Pinning the kubedev version')

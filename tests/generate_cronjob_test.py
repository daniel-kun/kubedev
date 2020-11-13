import unittest

import yaml
from kubedev import Kubedev
from test_utils import EnvMock, FileMock, TemplateMock, testCronJobConfig


class KubeDevGenerateCronJobTests(unittest.TestCase):
  def test_cronjob_deployyaml(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testCronJobConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    testCronJobYaml = fileMock.load_file(
        'helm-chart/templates/cronjobs/foo-job.yaml')

    self.assertIsNotNone(
        testCronJobYaml, 'helm-chart/templates/cronjobs/foo-job.yaml was not generated.')
    testCronJob = yaml.safe_load(testCronJobYaml)
    self.assertEqual(testCronJob['apiVersion'], 'batch/v1beta1')
    self.assertEqual(testCronJob['kind'], 'CronJob')
    self.assertEqual(testCronJob['metadata']['name'], "foo-service-foo-job")
    labels = testCronJob['metadata']['labels']
    self.assertEqual(labels['kubedev-app'], "foo-service")
    self.assertEqual(labels['kubedev-cronjob'], "foo-service-foo-job")
    templatePart = testCronJob['spec']['jobTemplate']['spec']['template']
    templateLabels = templatePart['metadata']['labels']
    self.assertEqual(templateLabels['kubedev-app'], "foo-service")
    self.assertEqual(
        templateLabels['kubedev-cronjob'], "foo-service-foo-job")
    containersPart = templatePart['spec']['containers']
    self.assertEqual(1, len(containersPart))
    containerPart = containersPart[0]
    self.assertEqual(
        containerPart['image'], 'foo-registry/foo-service-foo-job:{{.Values.KUBEDEV_TAG}}')

  def test_cronjob_envs(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()

    # ACT
    sut = Kubedev()
    sut.generate_from_config(
        testCronJobConfig, False, file_accessor=fileMock, env_accessor=envMock, template_accessor=TemplateMock())

    # ASSERT
    testCronJobYaml = fileMock.load_file(
        'helm-chart/templates/cronjobs/foo-job.yaml')
    testCronJob = yaml.safe_load(testCronJobYaml)
    container0 = testCronJob['spec']['jobTemplate']['spec']['template']['spec']['containers'][0]
    self.assertIn('env', container0)
    envs = container0['env']
    self.assertEqual(3, len(envs))
    envs = container0['env']
    self.assertIn(
        {'name': 'FOO_SERVICE_GLOBAL_ENV1',
          'value': '{{.Values.FOO_SERVICE_GLOBAL_ENV1}}'},
        [env for env in envs if env['name'] == 'FOO_SERVICE_GLOBAL_ENV1'])
    self.assertListEqual(
        [{'name': 'FOO_SERVICE_JOB_ENV1',
          'value': '{{.Values.FOO_SERVICE_JOB_ENV1}}'}],
        [env for env in envs if env['name'] == 'FOO_SERVICE_JOB_ENV1'])
    self.assertListEqual(
        [{'name': 'FOO_SERVICE_JOB_ENV2',
          'value': '{{.Values.FOO_SERVICE_JOB_ENV2}}'}],
        [env for env in envs if env['name'] == 'FOO_SERVICE_JOB_ENV2'])


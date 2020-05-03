import unittest

import yaml

from kubedev import Kubedev
from test_utils import EnvMock, FileMock, testDeploymentConfig


class KubeDevGenerateTiltfile(unittest.TestCase):

  def test_tiltfile_exists(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()

    # ACT
    sut = Kubedev('./templates/')
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock)

    # ASSERT
    tiltYaml = fileMock.load_file('Tiltfile')
    self.assertIsNotNone(tiltYaml)

  def test_tiltfile_docker_builds(self):
    # ARRANGE
    fileMock = FileMock()
    envMock = EnvMock()

    # ACT
    sut = Kubedev('./templates/')
    sut.generate_from_config(
        testDeploymentConfig, False, file_accessor=fileMock, env_accessor=envMock)

    # ASSERT
    tiltfile = fileMock.load_file('Tiltfile')
    self.assertIsNotNone(tiltfile)

    self.assertIn(
        "docker_build('foo-registry/foo-service-foo-deploy', 'foo-deploy')", tiltfile)
    self.assertIn("k8s_yaml(local('kubedev template'))", tiltfile)
    self.assertIn(
        "k8s_resource('foo-deploy', port_forwards=['8083:8082','8643:8543'])", tiltfile)

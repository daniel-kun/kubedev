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
    self.assertIsNotNone(fileMock.load_file('foo-deploy/Dockerfile'))

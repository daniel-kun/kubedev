import unittest
from kubedev import Kubedev

class FileMock:
  def __init__(self):
    self.files = dict()

  def load_file(self, filename):
    if filename in self.files:
      return self.files[filename]
    else:
      return None    

  def save_file(self, filename, content):
    self.files[filename] = content  

class KubeDevGenerateBasicTests(unittest.TestCase):

  def test_deployment_chartYaml(self):
    # ARRANGE
    fileMock = FileMock()
    with open('tests/test_deployment_basic.json') as f:
      fileMock.save_file('kubedev.json', f.read())

    # ACT
    sut = Kubedev()
    sut.generate(file_accessor = fileMock)

    # ASSERT
    chartYaml = fileMock.load_file('helm-chart/Chart.yaml')

    self.assertIsNotNone(chartYaml, 'helm-chart/Chart.yaml was not generated.')

  def test_deployment_chartYaml(self):
    # ARRANGE
    fileMock = FileMock()
    with open('tests/test_deployment_basic.json') as f:
      fileMock.save_file('kubedev.json', f.read())

    # ACT
    sut = Kubedev()
    sut.generate(file_accessor = fileMock)

    # ASSERT
    chartYaml = fileMock.load_file('helm-chart/Chart.yaml')
    testDeployYaml = fileMock.load_file('helm-chart/templates/deployments/testdeploy.yaml')
    tiltFile = fileMock.load_file('Tiltfile')
    gitlabCiYaml = fileMock.load_file('.gitlab-ci.yml')

    self.assertIsNotNone(chartYaml, 'helm-chart/Chart.yaml was not generated.')
    self.assertIsNotNone(testDeployYaml, 'helm-chart/templates/deployments/testdeploy.yaml was not generated.')
    self.assertIsNotNone(tiltFile, 'Tiltfile was not generated')
    self.assertIsNotNone(gitlabCiYaml, '.gitlab-ci.yml was not generated')

  def test_deployment_testdeployyaml(self):
    # ARRANGE
    fileMock = FileMock()
    with open('tests/test_deployment_basic.json') as f:
      fileMock.save_file('kubedev.json', f.read())

    # ACT
    sut = Kubedev()
    sut.generate(file_accessor = fileMock)

    # ASSERT
    testDeployYaml = fileMock.load_file('helm-chart/templates/deployments/testdeploy.yaml')

    self.assertIsNotNone(testDeployYaml, 'helm-chart/templates/deployments/testdeploy.yaml was not generated.')

  def test_deployment_tiltfile(self):
    # ARRANGE
    fileMock = FileMock()
    with open('tests/test_deployment_basic.json') as f:
      fileMock.save_file('kubedev.json', f.read())

    # ACT
    sut = Kubedev()
    sut.generate(file_accessor = fileMock)

    # ASSERT
    tiltFile = fileMock.load_file('Tiltfile')

    self.assertIsNotNone(tiltFile, 'Tiltfile was not generated')

  def test_deployment_gitlabci(self):
    # ARRANGE
    fileMock = FileMock()
    with open('tests/test_deployment_basic.json') as f:
      fileMock.save_file('kubedev.json', f.read())

    # ACT
    sut = Kubedev()
    sut.generate(file_accessor = fileMock)

    # ASSERT
    gitlabCiYaml = fileMock.load_file('.gitlab-ci.yml')

    self.assertIsNotNone(gitlabCiYaml, '.gitlab-ci.yml was not generated')


class ShellExecutorMock:
  def __init__(self):
    self._calls = []

  def execute(self, commandWithArgs, envVars):
    self._calls.append({'cmd': commandWithArgs, 'env': envVars})

  def calls(self):
    return self._calls


class FileMock:
  def __init__(self):
    self.files = dict()

  def load_file(self, filename):
    if filename in self.files:
      return self.files[filename]
    else:
      return None

  def save_file(self, filename, content, overwrite):
    if overwrite or not filename in self.files:
      self.files[filename] = content
      return True
    else:
      return False

  def mkdirhier(self, path):
    return None


class EnvMock:
  def __init__(self):
    self.envs = dict()

  def getenv(self, name):
    if name in self.envs:
      return self.envs[name]
    else:
      return None

  def setenv(self, name, value):
    self.envs[name] = value

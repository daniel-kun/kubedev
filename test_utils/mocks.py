import os


class ShellExecutorMock:
  def __init__(self, is_tty=False):
    self._calls = []
    self._is_tty = is_tty

  def execute(self, commandWithArgs, envVars):
    self._calls.append({'cmd': commandWithArgs, 'env': envVars})
    return 0

  def is_tty(self):
    return self._is_tty

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

  def getenv(self, name, default=None):
    if name in self.envs:
      return self.envs[name]
    else:
      return default

  def setenv(self, name, value):
    self.envs[name] = value


class TemplateMock:
  def load_template(self, file):
    with open(os.path.join('kubedev', 'templates', file), 'br') as f:
      return f.read()


class OutputMock:
  def __init__(self):
    self._prints = []

  def print(self, message, isError):
    self._prints.append({"message": message, "isError": isError})

  def messages(self):
    return self._prints

class TagGeneratorMock:
  def __init__(self, tags):
    self._tags = tags
    self._current = 0

  def tag(self):
    result = self._tags[self._current]
    self._current = self._current + 1
    if self._current >= len(self._tags):
      self._current = 0
    return result

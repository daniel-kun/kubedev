import os


class SleepMock:
  def sleep(self, seconds: float):
    return None

class ShellExecutorMock:
  def __init__(self, is_tty=False, cmd_output: list = []):
    self._calls = []
    self._is_tty = is_tty
    self._cmd_output = cmd_output

  def execute(self, commandWithArgs, envVars=dict(), piped_input: str = None, check=False):
    self._calls.append({'cmd': [cmd for cmd in commandWithArgs if cmd is not None], 'env': envVars, 'withOutput': False, 'pipedInput': piped_input})
    return 0

  def get_output(self, commandWithArgs, envVars: dict = dict(), check=False):
    self._calls.append({'cmd': [cmd for cmd in commandWithArgs if cmd is not None], 'env': envVars, 'withOutput': True})
    if len(self._cmd_output) > 0:
      result = self._cmd_output[0]
      self._cmd_output = self._cmd_output[1:]
      return result
    else:
      raise Exception('Not enough command output provided in ShellExcutorMock')

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

  def abspath(self, path):
    if os.path.isabs(path):
      return path
    else:
      return os.path.join("/kubedev/systemtests/", path)

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

  def environ(self):
    return self.envs


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

class DownloadMock:
  def __init__(self, success: bool, file_content: str):
    self._success = success
    self._file_content = file_content
    self._calls = []

  def download_file_to(self, url: str, headers: dict, target_filename: str, file_accessor) -> bool:
    self._calls.append([url, headers, target_filename])
    if self._success:
      file_accessor.save_file(target_filename, self._file_content, True)
      return True
    else:
      return False

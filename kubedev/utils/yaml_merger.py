import ruamel.yaml

# https://stackoverflow.com/questions/40235554/python-use-pyyaml-and-keep-format


def _find_first_of_type(_list, _type):
  for item in _list:
    if isinstance(item, _type):
      return item
  return None


def _is_marked_as_overwrite(mergeObject, key):
  if hasattr(mergeObject, 'ca'):
    if hasattr(mergeObject.ca, 'items'):
      if key in mergeObject.ca.items:
        tokens = mergeObject.ca.items[key]
        commentToken = _find_first_of_type(tokens, ruamel.yaml.CommentToken)
        if not isinstance(commentToken, type(None)):
          comment = commentToken.value
          if 'OVERWRITE' in comment:
            return True
  return False


def _merge_dicts(source, mergeObject):
  if isinstance(source, type(None)):
    source = dict()
  for (key, item) in mergeObject.items():
    if not key in source:
      if isinstance(item, dict):
        # Strip meta-information like comments:
        source[key] = dict()
        _merge_dicts(source[key], item)
      else:
        source[key] = item
    else:
      if isinstance(item, dict):
        if isinstance(source[key], dict):
          _merge_dicts(source[key], item)
        else:
          pass  # Can't merge an object from mergeObject into a scalar value in source
      elif _is_marked_as_overwrite(mergeObject, key):
        source[key] = item
      else:
        pass  # Don't overwrite existing scalar values if `overwrite` is not True
  return source


class YamlMerger:
  @staticmethod
  def merge(sourceYaml, mergeObject):
    if isinstance(sourceYaml, str):
      src = ruamel.yaml.round_trip_load(sourceYaml)
    else:
      src = sourceYaml
    if isinstance(mergeObject, str):
      merge = ruamel.yaml.round_trip_load(mergeObject)
    else:
      merge = mergeObject
    return _merge_dicts(src, merge)
#    return ruamel.yaml.round_trip_dump(result)

  @staticmethod
  def dump(o):
    return ruamel.yaml.round_trip_dump(o)

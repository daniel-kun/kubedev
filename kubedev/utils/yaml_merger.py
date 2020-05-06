import ruamel.yaml

# https://stackoverflow.com/questions/40235554/python-use-pyyaml-and-keep-format

# conf = open("results.conf", "r")
# results = ruamel.yaml.load(conf, ruamel.yaml.RoundTripLoader)
# conf.close()
# results['nas']['mount_dirs'][0] = "haha"
# with open('/home/zonion/speedio/speedio.conf', 'w') as conf:
#   ruamel.yaml.dump(results, conf, ruamel.yaml.RoundTripDumper)


def _merge_dicts(source, mergeObject, overwrite):
  for (key, item) in mergeObject.items():
    if not key in source:
      source[key] = item
    else:
      if isinstance(item, dict):
        if isinstance(source[key], dict):
          _merge_dicts(source[key], item, overwrite)
        else:
          pass  # Can't merge an object from mergeObject into a scalar value in source
      elif overwrite:
        source[key] = item
      else:
        pass  # Don't overwrite existing scalar values if `overwrite` is not True
  return source


class YamlMerger:
  @staticmethod
  def merge_keep_conflicts(sourceYaml, mergeObject):
    src = ruamel.yaml.round_trip_load(sourceYaml)
    result = _merge_dicts(src, mergeObject, False)
    return ruamel.yaml.round_trip_dump(result)

  @staticmethod
  def merge_overwrite_conflicts(sourceYaml, mergeObject):
    src = ruamel.yaml.round_trip_load(sourceYaml)
    result = _merge_dicts(src, mergeObject, True)
    return ruamel.yaml.round_trip_dump(result)

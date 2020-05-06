import unittest

from kubedev.utils import YamlMerger


class YamlMergerTests(unittest.TestCase):

  def test_merge_overwrite_conflicts(self):
    source = '''foo: Bar
'''
    result = YamlMerger.merge_overwrite_conflicts(source, {
        'foo': 'Baz',
        'bar': 'Boo'
    })

    self.assertEqual('''foo: Baz
bar: Boo
''', result)

  def test_merge_keep_conflicts(self):
    source = '''foo: Bar
'''
    result = YamlMerger.merge_keep_conflicts(source, {
        'foo': 'Baz',
        'bar': 'Boo'
    })

    self.assertEqual('''foo: Bar
bar: Boo
''', result)

  def test_merge_tree_keep_conflicts(self):
    source = '''root:
  a: 1
  b: 2
  node:
    x: 10
    y: 11
'''
    result = YamlMerger.merge_keep_conflicts(source, {
        'root': {
            'b': 99,
            'c': 3,
            'node': {
                'x': 98,
                'z': 12
            }
        }
    })

    self.assertEqual('''root:
  a: 1
  b: 2
  node:
    x: 10
    y: 11
    z: 12
  c: 3
''', result)

  def test_merge_tree_overwrite_conflicts(self):
    source = '''root:
  a: 1
  b: 2
  node:
    x: 10
    y: 11
'''
    result = YamlMerger.merge_overwrite_conflicts(source, {
        'root': {
            'b': 99,
            'c': 3,
            'node': {
                'x': 98,
                'z': 12
            }
        }
    })

    self.assertEqual('''root:
  a: 1
  b: 99
  node:
    x: 98
    y: 11
    z: 12
  c: 3
''', result)

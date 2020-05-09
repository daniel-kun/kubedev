import unittest

from kubedev.utils import YamlMerger


class YamlMergerTests(unittest.TestCase):

  def test_merge_overwrite_conflicts(self):
    source = '''foo: Bar
'''
    result = YamlMerger.merge(source, '''foo: Baz # OVERWRITE
bar: Boo
''')

    self.assertEqual('''foo: Baz
bar: Boo
''', YamlMerger.dump(result))

  def test_merge_keep_conflicts(self):
    source = '''foo: Bar
'''
    result = YamlMerger.merge(source, '''foo: Baz
bar: Boo
''')

    self.assertEqual('''foo: Bar
bar: Boo
''', YamlMerger.dump(result))

  def test_merge_tree_keep_conflicts(self):
    source = '''root:
  a: 1
  b: 2
  node:
    x: 10
    y: 11
'''
    result = YamlMerger.merge(source, '''root:
  b: 99
  c: 3
  node:
    x: 98
    z: 12
''')

    self.assertEqual('''root:
  a: 1
  b: 2
  node:
    x: 10
    y: 11
    z: 12
  c: 3
''', YamlMerger.dump(result))

  def test_merge_tree_overwrite_conflicts(self):
    source = '''root:
  a: 1
  b: 2
  node:
    x: 10
    y: 11
'''
    result = YamlMerger.merge(source, '''root:
  b: 99 # OVERWRITE
  c: 3
  node:
    x: 98 # OVERWRITE
    z: 12
''')

    self.assertEqual('''root:
  a: 1
  b: 99
  node:
    x: 98
    y: 11
    z: 12
  c: 3
''', YamlMerger.dump(result))

  def test_merge_dont_keep_comments_from_template(self):
    source = '''root:
  a: 1
  node1:
    x: 11
'''
    result = YamlMerger.merge(source, '''root:
  a: 99 # OVERWRITE
  b: 99 # OVERWRITE
  node1:
    x: 98 # OVERWRITE
    y: 12 # OVERWRITE
  node2:
    x: 98 # OVERWRITE
    y: 12 # OVERWRITE
''')

    self.assertEqual('''root:
  a: 99
  node1:
    x: 98
    y: 12
  b: 99
  node2:
    x: 98
    y: 12
''', YamlMerger.dump(result))

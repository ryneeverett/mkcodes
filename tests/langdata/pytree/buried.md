# Test discovery

For test discovery to work for unittest, python files generated from this document must have an `__init__.py` file added to the directory - otherwise they won't be considered testable packages.

```python
import unittest

class TestDiscovery(unittest.TestCase):
  def test_discovery(self):
    self.assertTrue(True)

```

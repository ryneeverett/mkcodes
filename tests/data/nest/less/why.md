# why?

Tests need to work even when the same filename is in multiple directories.

```py
import unittest

class TestLess(unittest.TestCase):
    def test_less(self):
        self.assertTrue(True)
```

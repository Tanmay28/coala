from queue import Queue
import sys
import unittest

sys.path.insert(0, ".")
from bears.tests.LocalBearTestHelper import LocalBearTestHelper
from bears.linters.PyRemoveCodeCommentBear import PyRemoveCodeCommentBear
from coalib.settings.Section import Section


class PyRemoveCodeCommentBearTest(LocalBearTestHelper):
    def setUp(self):
        self.uut = PyRemoveCodeCommentBear(Section('name'), Queue())

    def test_valid(self):
        self.assertLinesValid(self.uut, ["import sys"])
        self.assertLinesValid(self.uut, ["a = 1 + 1"])
        self.assertLinesValid(self.uut, ["# hey man!"])
        self.assertLinesValid(self.uut, ['"""',
                                         'Hey, this is a code sample:',
                                         '>>> import os',
                                         '',
                                         'And when you use it you can simply '
                                         'do: `import os`.',
                                         '"""'])

    def test_invalid(self):
        self.assertLinesInvalid(self.uut, ["# import os"])
        self.assertLinesInvalid(self.uut, ["# print('comment')"])


if __name__ == '__main__':
    unittest.main(verbosity=2)

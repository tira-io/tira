from abc import ABC, abstractmethod
from typing import Optional
from unittest.util import _common_shorten_repr


class StrAssertMixins(ABC):
    """A mixin class for adding further string related assertions to a test case.

    The inheriting class must implement ``fail`` and ``_formatMessage`` methods, which behave similar to
    `unittest.TestCase`. The most straight forward way is to use the mixin together with a `unittest.TestCase`:

    .. code:: python

       from unittest import TestCase

       class MyTest(TestCase, StrAssertMixins):

           def testcase(self):
               self.assertStartsWith("foobar", "foo")  # Success
               self.assertStartsWith("foobar", "bar")  # Fail
    """

    @abstractmethod
    def _formatMessage(self, msg: "Optional[str]", standardMsg: str) -> str: ...

    @abstractmethod
    def fail(self, msg: "Optional[str]" = None) -> None: ...

    def assertStartsWith(self, string: str, prefix: str, msg: "Optional[str]" = None) -> None:
        if not string.startswith(prefix):
            standardMsg = "not %s.startswith(%s)" % _common_shorten_repr(string, prefix)
            msg = self._formatMessage(msg, standardMsg)
            self.fail(msg)

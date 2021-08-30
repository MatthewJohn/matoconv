
from unittest import TestCase, mock

from matoconv import FormatFactory


class TestFormatFactory(TestCase):

    def setUp(self) -> None:
        self.format_factory = FormatFactory()
        return super().setUp()

    def test_unknown_format(self) -> None:
        form = self.format_factory.by_extension('doesnotexist')
        self.assertEqual(form, None)


from unittest import TestCase, mock

from matoconv import FormatFactory, PDF, ODT, DOC, DOCX, HTML


class TestFormatFactory(TestCase):

    def setUp(self) -> None:
        self.format_factory = FormatFactory()
        self.format_factory.register_formats()
        return super().setUp()

    def test_by_extension_unknown(self) -> None:
        """Test by_extension with an unknown extension."""
        form = self.format_factory.by_extension('doesnotexist')
        self.assertEqual(form, None)

    def test_by_extension(self):
        """Test by_extension method."""
        for ext, cls in [
                ['pdf', PDF], ['docx', DOCX],
                ['doc', DOC], ['html', HTML],
                ['odt', ODT]]:
            self.assertIsInstance(
                self.format_factory.by_extension(ext),
                cls
            )

    def test_by_extension_capital(self):
        """Test by_extension providing a capitalised extension."""
        for ext, cls in [
                ['PDF', PDF], ['DOCX', DOCX],
                ['DOC', DOC], ['HTML', HTML],
                ['ODT', ODT]]:
            self.assertIsInstance(
                self.format_factory.by_extension(ext),
                cls
            )

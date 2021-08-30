
from unittest import TestCase, mock

from matoconv import FormatFactory, PDF, ODT, DOC, DOCX, HTML


class TestByExtension(TestCase):

    def setUp(self) -> None:
        self.format_factory = FormatFactory()
        self.format_factory.register_formats()
        return super().setUp()

    def test_by_extension_unknown(self) -> None:
        """Test by_extension with an unknown extension."""
        form = self.format_factory.by_extension('doesnotexist')
        self.assertEqual(form, None)

    def test_by_extension_empty(self) -> None:
        """Test by_extension with an empty extension."""
        form = self.format_factory.by_extension('')
        self.assertEqual(form, None)

    def test_by_extension_mocked(self):
        """Test by_extension, mocking list of extensions and format class."""
        mocked_extension = mock.Mock()
        mocked_extension_instance = mock.Mock()
        mocked_extension.return_value = mocked_extension_instance

        FormatFactory.FORMATS = [mocked_extension]
        mocked_extension_instance.extension = 'tst'

        self.assertEqual(
            self.format_factory.by_extension('tst'),
            mocked_extension_instance)

        mocked_extension.assert_called()

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

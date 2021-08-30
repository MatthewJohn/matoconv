
from unittest import TestCase, mock

from matoconv import Matoconv


# Mock Pool, as teardown causes errors in __del__
@mock.Mock('matoconv.Pool')
class TestGetInstance(TestCase):

    def setUp(self) -> None:
        """Store current value of Matoconve INSTANCE static value."""
        self.original_matoconv_instance_value = Matoconv.INSTANCE
        return super().setUp()

    def tearDown(self) -> None:
        """Remove any cached version so Matoconv"""
        Matoconv.INSTANCE = self.original_matoconv_instance_value
        return super().tearDown()

    def test_get(self):
        """
        Ensure exception is raised when attempting to get_instance without creating.
        """
        # Ensure there is no cached version
        self.assertEqual(Matoconv.INSTANCE, None)
        matoconv = Matoconv.get_instance()
        # Ensure returned instance is an instance of Matoconv
        self.assertIsInstance(matoconv, Matoconv)

        # Ensure instance is cached.
        self.assertEqual(Matoconv.INSTANCE, matoconv)

        # Attemp to obtain again
        matoconv_2 = Matoconv.get_instance()
        # Ensure returned instance is an instance of Matoconv
        self.assertIsInstance(matoconv_2, Matoconv)

        # Ensure instances are the same
        self.assertEqual(matoconv, matoconv_2)

        # Ensure instance is cached.
        self.assertEqual(Matoconv.INSTANCE, matoconv_2)



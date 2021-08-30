
from unittest import TestCase

from matoconv import Matoconv, SingletonNotInstanciatedError


class TestGetInstance(TestCase):

    def setUp(self) -> None:
        """Store current value of Matoconve INSTANCE static value."""
        self.original_matoconv_instance_value = Matoconv.INSTANCE
        return super().setUp()

    def tearDown(self) -> None:
        """Remove any cached version so Matoconv"""
        Matoconv.INSTANCE = self.original_matoconv_instance_value
        return super().tearDown()

    def test_get_without_create(self):
        """
        Ensure exception is raised when attempting to get_instance without creating.
        """
        self.assertEqual(Matoconv.INSTANCE, None)
        with self.assertRaises(SingletonNotInstanciatedError):
            Matoconv.get_instance(create=False)
        self.assertEqual(Matoconv.INSTANCE, None)

    def test_get(self):
        """
        Ensure exception is raised when attempting to get_instance without creating.
        """
        # Ensure there is no cached version
        self.assertEqual(Matoconv.INSTANCE, None)
        matoconv = Matoconv.get_instance(create=True)
        # Ensure returned instance is an instance of Matoconv
        self.assertIsInstance(matoconv, Matoconv)

        # Ensure instance is cached.
        self.assertEqual(Matoconv.INSTANCE, matoconv)


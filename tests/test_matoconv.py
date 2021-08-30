
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
        Check that the get_instance method works as expected..
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


class TestRouteBase(TestCase):

    def setUp(self) -> None:
        """Create test instance of Matoconv"""
        # Create instance of Matoconv
        self.matoconv = Matoconv()
        # Update flask app config for testing
        self.matoconv.app.config['TESTING'] = True
        self.matoconv.app.config['WTF_CSRF_ENABLED'] = False
        self.matoconv.app.config['DEBUG'] = False

        self.client = self.matoconv.app.test_client()
        return super().setUp()


class TestRouteIndex(TestRouteBase):

    def test_index(self):
        """Test index."""
        with self.client.get('/') as res:
            self.assertTrue('Matoconv' in str(res.data))
            self.assertTrue('<textarea' in str(res.data))


class TestRouteConvert(TestRouteBase):

    def test_unknown_destination_format(self):
        """Test conversion of unknown destination format."""
        with self.client.post('/convert/format/doesnotexist',
                              headers={'Content-Disposition': 'attachment; filename="example.html"'},
                              data='NotRealData') as res:
            self.assertEqual(res.status_code, 404)

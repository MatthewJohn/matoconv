import warnings

from unittest import TestCase, mock

from matoconv import Matoconv, PDF, HTML


class TestRouteBase(TestCase):

    def create_matoconv_object(self):
        """Create test instance of Matoconv"""
        # Create instance of Matoconv
        self.matoconv = Matoconv()

        # Update flask app config for testing
        self.matoconv.app.config['TESTING'] = True
        self.matoconv.app.config['WTF_CSRF_ENABLED'] = False
        self.matoconv.app.config['DEBUG'] = False

    def create_test_client(self):
        """Create client for running test requests."""
        self.client = self.matoconv.app.test_client()

    def setUp(self) -> None:
        """Create required mocks/objects for tests."""
        self.create_matoconv_object()
        self.create_test_client()


class MockConversionDetails(object):

    """Type ID to be set by tests for specifying details."""
    TYPE = None

    """Property values, indexed by TYPE"""
    _VALUES = {
        1: {
            "original_filename": "OR1g1nalFILENAME.html",
            "response_mime_type": "special-type/pdf-mime",
            "t_input_path": "/tmp/conversion-path/temp-conversion-file.html",
            "t_output_path": "/tmp/conversion-path/temp-conversion-file.pdf",
            "t_input_filename": "temp-conversion-file.html",
            "t_output_filename": "temp-conversion-file.pdf",
            "t_extless_filename": "temp-conversion-file",
            "t_extless_path": "/tmp/conversion-path/temp-conversion-file",
            "ouptut_filename": "OR1g1nalFILENAME.pdf",
            "temp_directory": "/tmp/conversion-path",
            "destination_format": PDF,
            "source_format": HTML
        }
    }

    def __getattribute__(self, name: str):
        """Lookup attribute in VALUES dict and return vale, if available."""
        if name != 'TYPE' and name != '_VALUES':
            if self.TYPE is None:
                warnings.warn('Type not set in MockConversionDetails')
            elif name in self._VALUES[self.TYPE]:
                return self._VALUES[self.TYPE][name] 
        return super().__getattribute__(name)


class TestRouteMockedBase(TestRouteBase):

    MOCK_APP = True
    MOCK_FORMAT_FACTORY_REGISTER_FORMATS = True
    MOCK_CORS = True
    MOCK_POOL = True
    MOCK_CONVERSION_DETAILS = True
    MOCK_FORMAT_FACTORY_BY_EXTENSION = True
    MOCK_OPEN = True
    MOCK_TEMPORARY_DIRECTORY = True

    def setUp(self) -> None:
        """Create mocks and call setup setup."""
        self.create_mocks()
        return super().setUp()

    def create_mocks(self):
        """
        Mock objects before Matoconv object is created in setUp.
        @TODO Do not inherit from TestRouteBase and move mocks to actual test.
        """
        if self.MOCK_FORMAT_FACTORY_REGISTER_FORMATS:
            self.mock_register_formats_patcher = mock.patch('matoconv.FormatFactory.register_formats')
            self.mock_register_formats = self.mock_register_formats_patcher.start()
            self.addCleanup(self.mock_register_formats_patcher.stop)

        if self.MOCK_FORMAT_FACTORY_BY_EXTENSION:
            self.mock_format_factory_by_extension_patcher = mock.patch('matoconv.FormatFactory.by_extension')
            self.mock_format_factory_by_extension = self.mock_format_factory_by_extension_patcher.start()
            self.addCleanup(self.mock_format_factory_by_extension_patcher.stop)

        if self.MOCK_APP:
            self.mock_flask_patcher = mock.patch('matoconv.FlaskNoName')
            self.mock_flask = self.mock_flask_patcher.start()
            self.mock_flask_app = mock.MagicMock()
            self.mock_flask.return_value = self.mock_flask_app
            self.addCleanup(self.mock_flask_patcher.stop)

        if self.MOCK_CORS:
            self.mock_cors_patcher = mock.patch('matoconv.CORS')
            self.mock_cors = self.mock_cors_patcher.start()
            self.addCleanup(self.mock_cors_patcher.stop)

        if self.MOCK_POOL:
            self.mock_pool_patcher = mock.patch('matoconv.Pool')
            self.mock_pool = self.mock_pool_patcher.start()
            self.addCleanup(self.mock_pool_patcher.stop)

        if self.MOCK_CONVERSION_DETAILS:
            self.mock_conversion_details_patcher = mock.patch('matoconv.ConversionDetails')
            self.mock_conversion_details = self.mock_conversion_details_patcher.start()
            self.addCleanup(self.mock_conversion_details_patcher.stop)

        if self.MOCK_OPEN:
            self.mock_open = mock.mock_open()
            self.mock_open_patcher = mock.patch('matoconv.open', self.mock_open, create=True)
            self.mock_open_patcher.start()
            self.addCleanup(self.mock_open_patcher.stop)

        if self.MOCK_TEMPORARY_DIRECTORY:
            self.mock_temporary_directory_factory = mock.MagicMock()
            self.mock_temporary_directory_patcher = mock.patch('matoconv.tempfile.TemporaryDirectory', self.mock_temporary_directory_factory)
            self.mock_temporary_directory_patcher.start()
            self.addCleanup(self.mock_temporary_directory_patcher.stop)
            self.mock_temporary_directory = mock.MagicMock()
            self.mock_temporary_directory_factory.return_value = self.mock_temporary_directory


class TestGetInstance(TestRouteMockedBase):

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


class TestSetup(TestRouteMockedBase):

    def test_ensure_format_factory_setup(self):
        """Ensure register formats was called."""
        self.mock_register_formats.assert_called()
        # Ensure FlaskNoName is build with correct name
        self.mock_flask.assert_called_with('matoconv')
        # Assert cors called with flask app and resource config
        self.mock_cors.assert_called_with(self.mock_flask_app, resources={r"*": {"origins": ""}})
        # Assert Pool is created with correct number for threads
        self.mock_pool.assert_called_with(processes=5)


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
            self.assertTrue(b'Invalid destination file format' in res.data)

    def test_missing_content_disposition_header(self):
        """Test request when missing content disposition header."""
        with self.client.post('/convert/format/docx',
                              headers={},
                              data='NotRealData') as res:
            self.assertEqual(res.status_code, 400)
            self.assertTrue(b'Missing Content-Disposition header' in res.data)


class TestRouteConvert(TestRouteMockedBase):

    MOCK_APP = False

    def test_unknown_destination_format(self):

        # Update conversion details mock init to return mock object
        MockConversionDetails.TYPE = 1
        self.mock_conversion_details.return_value = MockConversionDetails()

        destination_format_mock = mock.MagicMock()
        self.mock_format_factory_by_extension.return_value = destination_format_mock

        # Setup mocked temporary directory
        self.mock_temporary_directory.__enter__.return_value = '/some_temp-dir'

        with self.client.post('/convert/format/docx',
                              headers={'Content-Disposition': 'attachment; filename="OR1g1nalFILENAME.html"'},
                              data='SOME TEST DATA FROM INPUT HTML FILE') as res:
            self.assertEquals(res.status_code, 200)
            self.assertEquals(res.headers['Content-Disposition'], 'attachment; filename=OR1g1nalFILENAME.pdf')
            self.assertEquals(res.content_type, "special-type/pdf-mime")

        self.mock_format_factory_by_extension.assert_called_with('docx')
        self.mock_conversion_details.assert_called_with(
            content_disp_headers='attachment; filename="OR1g1nalFILENAME.html"',
            temp_directory='/some_temp-dir',
            dest_format=destination_format_mock
        )

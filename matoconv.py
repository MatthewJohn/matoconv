# -*- coding: utf-8 -*-

import os
import tempfile
import subprocess
import sys
import time
from multiprocessing import Pool, TimeoutError

import flask
from flask_cors import CORS


class Config(object):
    """Class to provide access to configurations."""

    MAX_ATTEMPTS = int(os.environ.get('MAX_ATTEMPTS', 1))
    MAX_CONVERTERS = int(os.environ.get('MAX_CONVERTERS', 5))
    POOL_CONVERT_TIMEOUT = int(os.environ.get('POOL_CONVERT_TIMEOUT', 60))
    RETRY_WAIT_PERIOD = int(os.environ.get('RETRY_WAIT_PERIOD', 1))
    EXECUTION_TIMEOUT = int(os.environ.get('EXECUTION_TIMEOUT', 20))


class Format(object):
    """Base class for handling details about file format"""

    CONTENT_TYPE = None
    EXTENSION = None
    INPUT_FILTER = None
    OUTPUT_FILTER = None

    @property
    def content_type(self):
        """Return content type."""
        return self.CONTENT_TYPE

    @property
    def extension(self):
        """Return extension."""
        return self.EXTENSION

    @property
    def input_filter(self):
        """Return input filter."""
        return self.INPUT_FILTER

    @property
    def output_filter(self):
        """Return output filter."""
        return self.OUTPUT_FILTER


class PDF(Format):
    """Format class for PDF format."""

    CONTENT_TYPE = 'application/pdf'
    EXTENSION = 'pdf'
    INPUT_FILTER = 'writer_pdf_import'
    OUTPUT_FILTER = 'pdf'


class DOCX(Format):
    """Format class for DOCX format."""

    CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    EXTENSION = 'docx'
    OUTPUT_FILTER = 'docx:Office Open XML Text'


class HTML(Format):
    """Format class for HTML format."""

    CONTENT_TYPE = 'text/html'
    EXTENSION = 'html'
    OUTPUT_FILTER = 'html:HTML (StarWriter):EmbedImages'


class FormatFactory(object):
    """Factory class for providing lookup of format classes."""

    FORMATS = []

    @staticmethod
    def _register_format(format_cls):
        """Register a format"""
        FormatFactory.FORMATS.append(format_cls)

    @staticmethod
    def register_formats():
        """Register all formats."""
        FormatFactory._register_format(PDF)
        FormatFactory._register_format(DOCX)
        FormatFactory._register_format(HTML)

    @staticmethod
    def by_extension(extension):
        """Return format based on extension"""
        # If extension is empty, return None
        if not extension:
            return None

        # Look through formats to matching extension
        for ext in FormatFactory.FORMATS:
            if ext().extension == extension:
                # Return instance of class, so that properties work
                return ext()

        # Default return None
        return None


class MatoconvException(Exception):
    """Base exception for matoconv."""

    pass


class UnknownFileTypeError(MatoconvException):
    """Unknown filetype."""

    pass


class CannotDetectFileTypeError(MatoconvException):
    """Cannot detect input file type"""

    pass


class SingletonNotInstanciatedError(MatoconvException):
    """Singleton instance has not been instanciated."""

    pass


class FlaskNoName(flask.Flask):
    """Remove server name header."""

    def process_response(self, response):
        """Override response to remove server name"""
        response.headers['server'] = __name__
        return(response)


class ConversionDetails(object):
    """Struct-like object for storing details
    about conversions, such as file paths."""

    def __init__(self, content_disp_headers, temp_directory, dest_format):
        """Setup member variables."""
        self._destination_format = dest_format
        self._content_disp_headers = content_disp_headers

        self._original_filename = None
        self._source_format = None
        try:
            # Example content-disposition header:
            #    attachment; filename="example.html"
            # Perform the following:
            #   Get data from latter half of header after semi-colon
            #   Strip white-space
            #   Split by equals '=' and take second element
            #   Remove any double-quotes
            self._original_filename = self._content_disp_headers.split(';')[1].strip().split('=')[1].replace('"', '')
            self._source_format = FormatFactory.by_extension(self._original_filename.split('.')[-1])
        except ValueError:
            raise CannotDetectFileTypeError('Cannot detect input file type')

        if self._source_format is None:
            raise UnknownFileTypeError('Unsupported source format')

        # Generate output filename, removing the extension from the original filename
        # and adding output filetype extension.
        self._ouptut_filename = '.'.join(self.original_filename.split('.')[:-1]) + '.' + self.destination_format.extension

        # Create temporary file names for connversion
        self._t_input_filename = 'conversion.' + self.source_format.extension
        self._t_output_filename = 'conversion.' + self.destination_format.extension

        # Store temporary working directory
        self._temp_directory = temp_directory

    def _prepend_path(self, filename):
        """Prepend filename with temporary directory."""
        return self._temp_directory + '/' + filename

    @property
    def original_filename(self):
        """Return the original filename."""
        return self._original_filename

    @property
    def response_mime_type(self):
        """Return response mime type."""
        return self._destination_format.content_type

    @property
    def t_input_path(self):
        """Property for full path of temporary input file."""
        return self._prepend_path(self._t_input_filename)
    
    @property
    def t_output_path(self):
        """Property for full path of temporary output file."""
        return self._prepend_path(self._t_output_filename)

    @property
    def t_input_filename(self):
        """Property for name of temporary input file."""
        return self._t_input_filename

    @property
    def t_output_filename(self):
        """Property for name of temporary output file."""
        return self._t_output_filename

    @property
    def ouptut_filename(self):
        """Property for name of output file to be returned."""
        return self._ouptut_filename

    @property
    def temp_directory(self):
        """Property for path of the temporary directory for working."""
        return self._temp_directory

    @property
    def destination_format(self):
        """Property for destination file format class."""
        return self._destination_format

    @property
    def source_format(self):
        """Property for source file format class."""
        return self._source_format


class Matoconv(object):

    INSTANCE = None
    DEST_FORMATS = {}

    def __init__(self):
        """Instantiate flask app, cors and conversion pool."""
        self.app = FlaskNoName(__name__)
        self.cors = CORS(self.app, resources={r"*": {"origins": ""}})
        self.converter_pool = Pool(processes=Config.MAX_CONVERTERS)

        FormatFactory.register_formats()

        @self.app.route('/convert/format/<dest_filetype>', methods=['POST'])
        def convert_file(dest_filetype):
            """Provide endpoint for converting files."""

            # Check valid destination format
            dest_format = FormatFactory.by_extension(dest_filetype)
            if dest_format is None:
                flask.abort(404)

            content_disp = flask.request.headers.get('Content-Disposition', None)

            with tempfile.TemporaryDirectory() as tempdir:

                conversion_details = ConversionDetails(
                    content_disp_headers=content_disp,
                    temp_directory=tempdir,
                    dest_format=dest_format)

                with open(conversion_details.t_input_path, 'wb') as fh:
                    fh.write(flask.request.get_data())

                t = self.converter_pool.apply_async(
                    self.perform_conversion, (conversion_details, ))

                # Wait for pool taks to complete and obtain logs from
                # response
                conv_logs = t.get(timeout=Config.POOL_CONVERT_TIMEOUT)

                for log in conv_logs:
                    Matoconv.log(log)

                # Get response data
                output_data = None
                with open(conversion_details.t_output_path, 'rb') as fh:
                    output_data = fh.read()

            # Create cusotm response to handle binary data from
            # converted file
            response = flask.make_response(output_data)
            response.content_type = conversion_details.response_mime_type

            # Add content disposition header for holding
            # output filename.
            response.headers.set(
                'Content-Disposition', 'attachment',
                filename=conversion_details.ouptut_filename)

            return response

        @self.app.route('/', methods=['GET'])
        def index():  # pragma: no cover
            return flask.send_from_directory('static', 'index.html')

    @staticmethod
    def log(msg):
        """Log using the flask error log method."""
        Matoconv.get_instance().app.logger.error(msg)

    @staticmethod
    def get_instance(create=False):
        """Obtain singleton instance of Mataconv."""
        if Matoconv.INSTANCE is None and create:
            Matoconv.INSTANCE = Matoconv()

        elif Matoconv.INSTANCE is None:
            raise SingletonNotInstanciatedError('No matoconv instance exists')

        return Matoconv.INSTANCE

    @staticmethod
    def perform_conversion(conversion_details):
        """Using libreoffice, convert file to destination format."""
        logs = []
        try:
            attempts = 0
            return_logs = False

            # Create argument for input filter, if one has been specified for the given
            # input format
            input_filter = (['--infilter=' + conversion_details.source_format.input_filter]
                            if conversion_details.source_format.input_filter else [])

            # Copy current environment variables
            env = dict(os.environ)
            # Add DISPLAY env variable
            env['DISPLAY'] = ':99'

            cmd = [
                'timeout', str(Config.EXECUTION_TIMEOUT) + 's',
                'soffice',
                '--headless',
                '--convert-to', conversion_details.destination_format.output_filter,
                ] + input_filter + [
                '-env:UserInstallation=file://' + conversion_details.temp_directory,
                '--writer',
                '--nocrashreport',
                '--nodefault',
                '--nofirststartwizard',
                '--nologo',
                '--norestore',
                conversion_details.t_input_path
            ]

            while attempts < Config.MAX_ATTEMPTS:
                logs.append('Running cmd:')
                logs.append(cmd)
                p = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    cwd=conversion_details.temp_directory,
                    env=env)

                # Capture response code, stdout and stderr
                rc = p.wait()
                logs.append('Got RC '  + str(rc))
                logs.append(p.stdout.read().decode(
                    'utf8', errors='backslashreplace').replace('\r', ''))
                logs.append(p.stderr.read().decode(
                    'utf8', errors='backslashreplace').replace('\r', ''))

                # If libreoffice returned ok status code and
                # the output file was created, break from loop
                if not rc and os.path.isfile(conversion_details.t_output_path):
                    break
                else:
                    return_logs = True

                # Remove output file if it was generated
                if os.path.isfile(conversion_details.t_output_path):
                    os.unlink(conversion_details.t_output_path)

                time.sleep(Config.RETRY_WAIT_PERIOD)

                attempts += 1
        except Exception as exc:
            # Add exception string to list of logs to be returned
            logs.append(str(exc))
            return_logs = True

        finally:
            # Only return logs if an error occured
            if return_logs:
                return logs
            else:
                return []


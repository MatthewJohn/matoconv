# -*- coding: utf-8 -*-

import os
import tempfile
import subprocess
import sys
import time
from multiprocessing import Pool, TimeoutError

import flask
from flask_cors import CORS


MAX_ATTEMPTS = int(os.environ.get('MAX_ATTEMPTS', 3))
MAX_CONVERTERS = int(os.environ.get('MAX_CONVERTERS', 5))
POOL_CONVERT_TIMEOUT = int(os.environ.get('POOL_CONVERT_TIMEOUT', 60))
RETRY_WAIT_PERIOD = int(os.environ.get('RETRY_WAIT_PERIOD', 1))
EXECUTION_TIMEOUT = int(os.environ.get('EXECUTION_TIMEOUT', 10))
VALID_DESTINATIONS = ['pdf', 'docx']


class ConversionDetails(object):
    """Struct-like object for storing details
    about conversions, such as file paths."""

    def __init__(self, content_disp_headers, temp_directory, dest_filetype):
        """Setup member variables."""
        self._original_filename = 'input.html'
        self._destination_filetype = dest_filetype
        self._content_disp_headers = content_disp_headers

        self._original_filename = 'input.html'
        try:
            # Example content-disposition header:
            #    attachment; filename="example.html"
            # Perform the following:
            #   Get data from latter half of header after semi-colon
            #   Strip white-space
            #   Split by equals '=' and take second element
            #   Remove any double-quotes
            self._original_filename = self._content_disp_headers.split(';')[1].strip().split('=')[1].replace('"', '')
        except ValueError:
            # If the heaader isn't in the right format, ignore it and
            # use default 'input.html'
            pass

        # Generate output filename, removing the extension from the original filename
        # and adding output filetype extension.
        self._ouptut_filename = '.'.join(self._original_filename.split('.')[:-1]) + '.' + self._destination_filetype

        # Create temporary file names for connversion
        self._t_input_filename = 'conversion.html'
        self._t_output_filename = 'conversion.' + self._destination_filetype

        # Store temporary working directory
        self._temp_directory = temp_directory

    def _prepend_path(self, filename):
        """Prepend filename with temporary directory."""
        return self._temp_directory + '/' + filename

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
    def destination_filetype(self):
        """Property for destination file type."""
        return self._destination_filetype


class Matoconv(object):

    INSTANCE = None

    def __init__(self):
        """Instantiate flask app, cors and conversion pool."""
        self.app = flask.Flask(__name__)
        self.cors = CORS(self.app, resources={r"*": {"origins": ""}})
        self.converter_pool = Pool(processes=MAX_CONVERTERS) 

        @self.app.route('/convert/format/<dest_filetype>', methods=['POST'])
        def convert_pdf(dest_filetype):
            """Provide endpoint for converting PDFs."""

            # Check valid destiation format
            if dest_filetype not in VALID_DESTINATIONS:
                flask.abort(404)

            content_disp = flask.request.headers.get('Content-Disposition', None)

            with tempfile.TemporaryDirectory() as tempdir:

                conversion_details = ConversionDetails(
                    content_disp_headers=content_disp,
                    temp_directory=tempdir,
                    dest_filetype=dest_filetype)

                with open(conversion_details.t_input_path, 'wb') as fh:
                    fh.write(flask.request.get_data())

                t = self.converter_pool.apply_async(
                    self.convert_file, (conversion_details, ))

                # Wait for pool taks to complete and obtain logs from
                # response
                conv_logs = t.get(timeout=POOL_CONVERT_TIMEOUT)

                for log in conv_logs:
                    Matoconv.log(log)

                # Get response data
                output_data = None
                with open(conversion_details.t_output_path, 'rb') as fh:
                    output_data = fh.read()

            # Create cusotm response to handle binary data from
            # converted file
            response = flask.make_response(output_data)

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
            raise Exception('No instance exists')
        return Matoconv.INSTANCE

    @staticmethod
    def convert_file(conversion_details):
        """Using libreoffice, convert input html to pdf."""
        logs = []
        try:
            attempts = 0
            return_logs = False
            cmd = [
                'timeout', str(EXECUTION_TIMEOUT) + 's',
                'soffice', '--headless',
                '--convert-to', conversion_details.destination_filetype,
                '-env:UserInstallation=file://' + conversion_details.temp_directory,
                '--writer',
                conversion_details.t_input_path
            ]

            while attempts < MAX_ATTEMPTS:
                logs.append('Running cmd:')
                logs.append(cmd)
                p = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    cwd=conversion_details.temp_directory)

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

                time.sleep(RETRY_WAIT_PERIOD)

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


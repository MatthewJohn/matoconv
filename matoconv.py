# -*- coding: utf-8 -*-

import os
import tempfile
import subprocess
import sys
import time
from multiprocessing import Pool, TimeoutError

import flask
from flask_cors import CORS


MAX_ATTEMPTS = 3
MAX_CONVERTERS = 5
CONVERTER_TIMEOUT = 5


class Matoconv(object):

    INSTANCE = None

    def __init__(self):
        self.app = flask.Flask(__name__)
        self.cors = CORS(self.app, resources={r"*": {"origins": "*"}})

        self.converter_pool = Pool(processes=MAX_CONVERTERS) 


        @self.app.route('/convert/format/pdf', methods=['POST'])
        def convert_pdf():
            content_disp = flask.request.headers.get('Content-Disposition', None)
            upload_filename = 'input.html'
            if content_disp and len(content_disp.split(';')) == 2:
                upload_filename = 'found.html'
            output_filename = '.'.join(upload_filename.split('.')[:-1]) + '.pdf'

            # Generate temp filename
            temp_fh = tempfile.NamedTemporaryFile()
            temp_filename = temp_fh.name
            temp_fh.close()

            # Create input/output filenames¦
            output_dir = os.path.dirname(temp_filename)
            t_input_filename = temp_filename + '.html'
            t_output_filename = temp_filename + '.pdf'

            with open(t_input_filename, 'wb') as fh:
                fh.write(flask.request.get_data())


            t = self.converter_pool.apply_async(self.convert_file, (t_input_filename, t_output_filename, output_dir))
            conv_logs = t.get()
            for log in conv_logs:
                Matoconv.log(log)

            # Get response data
            output_data = None
            with open(t_output_filename, 'rb') as fh:
                output_data = fh.read()

            # Remove old files
            os.unlink(t_input_filename)
            os.unlink(t_output_filename)

            response = flask.make_response(output_data)

            response.headers.set(
                'Content-Disposition', 'attachment', filename=output_filename)
            return response

    @staticmethod
    def log(msg):
        Matoconv.get_instance().app.logger.error(msg)

    @staticmethod
    def get_instance(create=False):
        if Matoconv.INSTANCE is None and create:
            Matoconv.INSTANCE = Matoconv()
        elif Matoconv.INSTANCE is None:
            raise Exception('No instance exists')
        return Matoconv.INSTANCE

    @staticmethod
    def convert_file(input_file, output_file, output_dir):
        logs = []
        try:
            attempts = 0
            cmd = [
                'soffice', '--headless',
                '--convert-to', 'pdf',
                '--writer',
                '--outdir', output_dir,
                input_file
            ]
            while attempts < MAX_ATTEMPTS:
                logs.append('Running cmd:')
                logs.append(cmd)
                p = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE)

                rc = p.wait()
                logs.append('Got RC '  + str(rc))
                logs.append(p.stdout.read().decode(
                    'utf8', errors='backslashreplace').replace('\r', ''))
                logs.append(p.stderr.read().decode(
                    'utf8', errors='backslashreplace').replace('\r', ''))
                if not rc:
                    break

                if os.path.isfile(output_file):
                    os.unlink(output_file)

                time.sleep(1)

                attempts += 1
        except Exception as exc:
            logs.append(exc)
        finally:
            return logs



import os
from unittest import TestCase, mock

import requests


class TestByExtension(TestCase):

    def _convert_file(self,file):
        pass

    def _screenshot_file(self, file):
        pass

    def _compare_files(self, file_a, file_b):
        pass

    def test_comparison(self):
        cwd = os.path.dirname(os.path.abspath(__file__))
        input_file = f"{cwd}/files/input_a.odt"
        output_file = f"{cwd}/files/output_a.docx"
        with open(input_file, 'rb') as fh:
            in_data = fh.read()
        res = requests.post(
            'http://localhost:8091/convert/format/docx',
            headers={'Content-Disposition': 'attachment; filename="input_a.odt"'},
            data=in_data)

        self.assertEqual(res.status_code, 200)
        print(dir(res))
        with open(output_file, 'wb') as fh:
            fh.write(res.content)


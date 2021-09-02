
import os
import subprocess

from PIL import Image

from matoconv import Matoconv
from tests.test_matoconv import TestRouteBase


class FileSpec(object):

    def __init__(self, name, input_extension, output_extension):
        self.name = name
        self.input_extension = input_extension
        self.output_extension = output_extension
        self.screenshot_extension = 'jpg'

    @property
    def cwd(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

    def full(self, file):
        return os.path.join(self.cwd, file)

    def templated_name(self, file_type, extension):
        return self.full(f'{file_type}_{self.name}.{extension}')

    @property
    def input_file(self):
        return self.templated_name('input', self.input_extension)

    @property
    def output_file(self):
        return self.templated_name('output', self.output_extension)

    @property
    def output_screenshot(self):
        return self.templated_name('output', self.screenshot_extension)

    @property
    def reference_output_screenshot(self):
        return self.templated_name('reference', self.screenshot_extension)

    @property
    def reference_deltas(self):
        return self.templated_name('reference', 'txt')

    @property
    def input_screenshot(self):
        return self.templated_name('input', self.screenshot_extension)


class TestByExtension(TestRouteBase):

    def _convert_file(self, file_spec: FileSpec):
        with open(file_spec.input_file, 'rb') as fh:
            in_data = fh.read()
        with self.client() as client:
            res = client.post(
                'http://localhost:8091/convert/format/docx',
                headers={'Content-Disposition': 'attachment; filename="input_a.odt"'},
                data=in_data)

        self.assertEqual(res.status_code, 200)

        with open(file_spec.output_file, 'wb') as fh:
            fh.write(res.content)

    def _screenshot_files(self, file_spec: FileSpec):
        for file_, extension in [
                [file_spec.input_file, file_spec.input_extension],
                [file_spec.output_file, file_spec.output_extension]]:
            if extension in ['doc', 'docx', 'odt']:
                proc = subprocess.Popen(['libreoffice', '--convert-to', 'jpg', file_], cwd=file_spec.cwd)
                rc = proc.wait()
                self.assertEqual(rc, 0)
                continue

    def _compare_files(self, file_spec: FileSpec):
        reference_image = Image.open(file_spec.reference_output_screenshot)
        test_image = Image.open(file_spec.output_screenshot)
        input_image = Image.open(file_spec.input_screenshot)

        width, height = test_image.size
        block_height = 20
        block_width = 20

        with open(file_spec.reference_deltas, 'r') as delta_fh:
            for y in range(0, height, block_height+1):
                for x in range(0, width, block_width+1):
                    pixels_reference = self.process_block(test_image, x, y, block_width, block_height)
                    pixels_test = self.process_block(reference_image, x, y, block_width, block_height)
                    pixels_input = self.process_block(input_image, x, y, block_width, block_height)

                    input_test_diff = pixels_input - pixels_test
                    #delta_fh.write(str(input_test_diff) + "\n")
                    self.assertEqual(int(delta_fh.readline()), input_test_diff)
                    self.assertEqual(pixels_reference, pixels_test)

    def process_block(self, image, x, y, width, height):
        total = 0
        for x_itx in range(width):
            for y_itx in range(height):
                try:
                    pixel = image.getpixel((x_itx + x, y_itx + y))
                    total += sum(pixel)
                except:
                    pass

        return total

    def test_comparison(self):

        file_spec = FileSpec('a', 'odt', 'docx')
        self._convert_file(file_spec)
        self._screenshot_files(file_spec)
        self._compare_files(file_spec)
        #self._compare_files(file_spec.input_screenshot, file_spec.output_screenshot)

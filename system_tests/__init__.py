
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

    def templated_name(self, file_type: str, extension: str, with_path: bool):
        file_ = f'{file_type}_{self.name}.{extension}'
        return self.full(file_) if with_path else file_

    @property
    def input_file(self):
        return self.templated_name('input', self.input_extension, with_path=False)

    @property
    def input_file_path(self):
        return self.templated_name('input', self.input_extension, with_path=True)

    @property
    def output_file_path(self):
        return self.templated_name('output', self.output_extension, with_path=True)

    @property
    def output_screenshot(self):
        return self.templated_name('output', self.screenshot_extension, with_path=True)

    @property
    def reference_output_screenshot(self):
        return self.templated_name('reference', self.screenshot_extension, with_path=True)

    @property
    def reference_deltas(self):
        return self.templated_name('input_output_diff', 'txt', with_path=True)

    @property
    def input_screenshot(self):
        return self.templated_name('input', self.screenshot_extension, with_path=True)


class TestByExtension(TestRouteBase):

    def _convert_file(self, file_spec: FileSpec):
        with open(file_spec.input_file_path, 'rb') as fh:
            in_data = fh.read()
        with self.client as client:
            res = client.post(
                f'http://localhost:8091/convert/format/{file_spec.output_extension}',
                headers={'Content-Disposition': f'attachment; filename="{file_spec.input_file}"'},
                data=in_data)

        self.assertEqual(res.status_code, 200)

        with open(file_spec.output_file_path, 'wb') as fh:
            fh.write(res.data)

    def _screenshot_files(self, file_spec: FileSpec):
        for file_, extension, screenshot_file in [
                [file_spec.input_file_path, file_spec.input_extension, file_spec.input_screenshot],
                [file_spec.output_file_path, file_spec.output_extension, file_spec.output_screenshot]]:
            if extension in ['doc', 'docx', 'odt']:
                cmd = ['libreoffice', '--convert-to', 'jpg', file_]

            elif extension in ['html']:
                cmd = ['chromium', '--headless', '--no-sandbox',
                       f'--screenshot={screenshot_file}', f'"file://{file_}"']

            else:
                cmd = ['convert', file_, screenshot_file]

            proc = subprocess.Popen(cmd, cwd=file_spec.cwd)
            rc = proc.wait()
            self.assertEqual(rc, 0)                

    def _compare_files(self, file_spec: FileSpec):
        reference_image = Image.open(file_spec.reference_output_screenshot)
        test_image = Image.open(file_spec.output_screenshot)
        input_image = Image.open(file_spec.input_screenshot)

        width, height = test_image.size
        block_height = 20
        block_width = 20


        pixels_reference = []
        pixels_test = []

        pixels_input_diff = []
        pixels_expected_input_diff = []
        with open(file_spec.reference_deltas, 'r') as delta_fh:
            for y in range(0, height, block_height+1):
                for x in range(0, width, block_width+1):
                    test_pixel = self.process_block(test_image, x, y, block_width, block_height)
                    pixels_test.append(test_pixel)
                    pixels_reference.append(self.process_block(reference_image, x, y, block_width, block_height))
                    pixels_input = self.process_block(input_image, x, y, block_width, block_height)

                    # Diff input file pixels and output file pixels
                    input_test_diff = pixels_input - test_pixel
                    pixels_input_diff.append(input_test_diff)
                    # Obtain expected diff of pixels between input and output file
                    # from reference_deltas file
                    #delta_fh.write(str(input_test_diff) + "\n")
                    pixels_expected_input_diff.append(int(delta_fh.readline()))
        self.assertEqual(pixels_reference, pixels_test)
        self.assertEqual(pixels_expected_input_diff, pixels_input_diff)

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

    def _perform_test(self, file_name, input_extension, output_extension):
            file_spec = FileSpec(file_name, input_extension, output_extension)
            self._convert_file(file_spec)
            self._screenshot_files(file_spec)
            self._compare_files(file_spec)

    def test_comparison_a_odt_docx(self):
        self._perform_test('a', 'odt', 'docx')

    def test_comparison_b_odt_doc(self):
        self._perform_test('b', 'odt', 'doc')

    def test_comparison_c_odt_pdf(self):
        self._perform_test('c', 'odt', 'pdf')

    def test_comparison_d_odt_html(self):
        self._perform_test('d', 'odt', 'html')

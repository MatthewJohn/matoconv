
from unittest import TestCase, mock

from matoconv import Matoconv


class TestMatoconv(TestCase):

    def test_matoconv(self):
        pass

    def client(self):
        matoconv = Matoconv()
        matoconv.app.config['TESTING'] = True
        with matoconv.app.test_client() as client:
            yield client


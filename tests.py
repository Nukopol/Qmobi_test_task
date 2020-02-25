import unittest
import urllib
import server
import sys
from threading import Thread

import subprocess

SERV_PORT = 53210

class Server_tests(unittest.TestCase):
    def setUp(self):
        self.theproc = subprocess.Popen([sys.executable, "server.py"])

    # Full correct request
    def test_main_func_true(self):
        response = urllib.request.urlopen("http://localhost:{}/converter?valute=USD&value=300".format(SERV_PORT))
        self.assertEqual(response.code, 200)

    # POST request
    def test_main_func_wrong_type(self):
        data = {}
        enc_data = urllib.parse.urlencode(data)
        try:
            response = urllib.request.urlopen("http://localhost:{}/converter?valute=USD&value=300".format(SERV_PORT), enc_data.encode('utf-8'))
            code = response.code
        except Exception as e:
            code = e.code
        self.assertNotEqual(code, 200)

    # Wrong valute name
    def test_main_func_wrong_valute(self):
        try:
            response = urllib.request.urlopen("http://localhost:{}/converter?valute=UShD&value=300".format(SERV_PORT))
            code = response.code
        except Exception as e:
            code = e.code
        self.assertNotEqual(code, 200)

    # String valute value
    def test_main_func_wrong_value(self):
        try:
            response = urllib.request.urlopen("http://localhost:{}/converter?valute=USD&value=3X00".format(SERV_PORT))
            code = response.code
        except Exception as e:
            code = e.code
        self.assertNotEqual(code, 200)

    # Wrong url path
    def test_main_func_wrong_path(self):
        try:
            response = urllib.request.urlopen("http://localhost:{}/Xconverter?valute=USD&value=300".format(SERV_PORT))
            code = response.code
        except Exception as e:
            code = e.code
        self.assertNotEqual(code, 200)

    # Without parameters
    def test_main_func_wrong_param(self):
        try:
            response = urllib.request.urlopen("http://localhost:{}/converter".format(SERV_PORT))
            code = response.code
        except Exception as e:
            code = e.code
        self.assertNotEqual(code, 200)

    def tearDown(self):
        self.theproc.kill()


if __name__ == '__main__':
    unittest.main()
import unittest
import urllib
import server
import sys
from threading import Thread

import subprocess

SERV_PORT = 53210

class Server_tests(unittest.TestCase):
    def setUp(self):
        self.proc = subprocess.Popen([sys.executable, "server.py"])

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

    # Test get rates from cbr.ru
    def test_get_rates(self):
        rates = server.Server.get_rates(self)
        flag = True
        if type(rates) is not dict:
            flag = False
        self.assertTrue(flag)

    # Full correct convert valute, value as int
    def test_conv_true(self):
        t_serv = server.Server()
        response = t_serv.converter("USD", 300)
        self.assertTrue(type(response) is dict)

    # Full correct convert valute, value as str
    def test_conv_value_str(self):
        t_serv = server.Server()
        response = t_serv.converter("USD", "300")
        self.assertTrue(type(response) is dict)

    # Full correct convert valute, value as float with point
    def test_conv_point(self):
        t_serv = server.Server()
        response = t_serv.converter("USD", 300.123)
        self.assertTrue(type(response) is dict)

    # Full correct convert valute, value as float with comma as string
    def test_conv_point_str(self):
        t_serv = server.Server()
        response = t_serv.converter("USD", "300,123")
        self.assertTrue(type(response) is dict)

    # Wrong valute name
    def test_conv_wrong_valute(self):
        t_serv = server.Server()
        response = t_serv.converter("XUSDX", 300)
        self.assertEqual(str(response), "Сouldn't find valute XUSDX")

    # Wrong value
    def test_conv_wrong_value(self):
        t_serv = server.Server()
        response = t_serv.converter("USD", "X300X")
        self.assertEqual(str(response), "could not convert string to float: 'X300X'")

    # Wrong valute name and value
    def test_conv_all_wrong(self):
        t_serv = server.Server()
        response = t_serv.converter("XUSDX", "X300X")
        self.assertEqual(str(response), "Сouldn't find valute XUSDX")

    def tearDown(self):
        self.proc.kill()


if __name__ == '__main__':
    unittest.main()
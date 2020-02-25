import json, socket, sys, urllib.request
from email.parser import Parser
from functools import lru_cache
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as etree
from datetime import datetime
import config


# type must be "ERROR", "LOG" or "DEBUG"
def logging(type, message):
    now = datetime.now()
    cur_datetime_str = now.strftime("%d.%m.%Y %H:%M:%S")

    if type == "ERROR" and config.LOG_LEVEL >= 1:
        print_mess = "{} - {} - {}\n".format(cur_datetime_str, type, message)
        sys.stdout.write(print_mess)
    if type == "LOG" and config.LOG_LEVEL >= 2:
        print_mess = "{} - {} - {}\n".format(cur_datetime_str, type, message)
        sys.stdout.write(print_mess)
    if type == "DEBUG" and config.LOG_LEVEL >= 3:
        print_mess = "{} - {} - {}\n".format(cur_datetime_str, type, message)
        sys.stdout.write(print_mess)


class Server:
    def __init__(self):
        self._port = config.PORT
        self.serve_forever()

    def serve_forever(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)

        try:
            # try to open socket
            serv_sock.bind(("", self._port))
            serv_sock.listen()

            while True:
                conn, _ = serv_sock.accept()
                try:
                  self.serve_client(conn)
                except (Exception) as error:
                  self.logging("ERROR", "Client serving failed" + str(error))
        finally:
            serv_sock.close()

    def serve_client(self, conn):
        try:
            req = self.parse_request(conn)
            logging("LOG", "target url: {} {}".format(req.method, req.target))
            resp = self.handle_request(req)
            self.send_response(conn, resp)
        except ConnectionResetError:
            conn = None
        except Exception as e:
            self.send_error(conn, e)

        if conn:
            req.rfile.close()
            conn.close()

    def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
        headers = self.parse_headers(rfile)
        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile):
        raw = rfile.readline(config.MAX_LINE + 1)
        if len(raw) > config.MAX_LINE:
            logging("ERROR", "Request line is too long")
            raise HTTPError(400, 'Bad request', 'Request line is too long')

        req_line = str(raw, 'iso-8859-1')
        words = req_line.split()
        if len(words) != 3:
            logging("ERROR", "Malformed request line")
            raise HTTPError(400, 'Bad request', 'Malformed request line')

        method, target, ver = words
        return method, target, ver

    def parse_headers(self, rfile):
        headers = []
        while True:
            line = rfile.readline(config.MAX_LINE + 1)
            if len(line) > config.MAX_LINE:
                raise HTTPError(494, 'Request header too large')

            if line in (b'\r\n', b'\n', b''):
                break

            headers.append(line)
        if len(headers) > config.MAX_HEADERS:
            raise HTTPError(494, 'Too many headers')

        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)

    def handle_request(self, req):
        if req.path == '/converter' and req.method == 'GET':
            return self.handle_get_converter(req)
        logging("ERROR", "wrong url: {} {}".format(req.method, req.path))
        raise HTTPError(404, 'Not found')

    def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))

        if resp.headers:
            for (key, value) in resp.headers:
                header_line = f'{key}: {value}\r\n'
                wfile.write(header_line.encode('iso-8859-1'))

        wfile.write(b'\r\n')

        if resp.body:
            wfile.write(resp.body)

        wfile.flush()
        wfile.close()

    def send_error(self, conn, err):
        try:
            status = err.status
            reason = err.reason
            body = (err.body or err.reason).encode('utf-8')
        except:
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        resp = Response(status, reason, [('Content-Length', len(body))], body)
        self.send_response(conn, resp)

    def handle_get_converter(self, req):
        contentType = 'application/json; charset=utf-8'

        if "valute" not in req.query or "value" not in req.query:
            logging("ERROR", "Missing request parameters")
            result = "Missing request parameters".encode('utf-8')
            headers = [('Content-Type', contentType),
                     ('Content-Length', len(result))]
            return Response(400, "Bad Request", headers, result)

        # get request parameters
        valute = req.query['valute'][0]
        value = req.query['value'][0]

        logging("DEBUG", "valute: " + str(valute))
        logging("DEBUG", "value: " + str(value))

        result = self.converter(valute, value)
        if type(result) is not dict:
            # if result isn't a dictionary, that mean result is the error
            result = str(result).encode('utf-8')
            headers = [('Content-Type', contentType),
                     ('Content-Length', len(result))]
            return Response(400, "Bad Request", headers, result)

        body = json.dumps(result)
        body = body.encode('utf-8')
        headers = [('Content-Type', contentType),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    def get_rates(self):
        try:
            valutes_response = urllib.request.urlopen("http://www.cbr.ru/scripts/XML_daily.asp?")
            valutes_tree = etree.parse(valutes_response)
            root = valutes_tree.getroot()

            # parse xml response from cbr.ru
            valutes_data = {}
            valutes_data["date"] = root.attrib["Date"]
            valutes_data["valCurs"] = {}

            for valute in root:
                code = next(valute.iter("CharCode"))
                value = next(valute.iter("Value"))
                nominal = next(valute.iter("Nominal"))
                f_value = float(value.text.replace(',', '.')) / float(nominal.text.replace(',', '.'))
                valutes_data["valCurs"][code.text] = f_value
        except (Exception) as error:
            logging("ERROR", str(error))
            return error
        return valutes_data

    def converter(self, valute, value):
        try:
            rates = self.get_rates()

            if type(rates) is not dict:
                raise Exception("Сouldn't get exchange rates")

            if valute not in rates["valCurs"]:
                raise Exception("Сouldn't find valute {}".format(valute))

            # create respose
            response = {}
            response["valute"] = valute
            response["rate"] = rates["valCurs"][valute]
            response["rate_date"] = rates["date"]
            response["req_value"] = valute

            # convert to RUB
            f_value = float(value.replace(',', '.'))
            result_value = round(f_value * rates["valCurs"][valute], 4)
            logging("DEBUG", "result valur: " + str(result_value))

            response["res_value"] = result_value
        except (Exception) as error:
            logging("ERROR", str(error))
            return error
        return response

class Request:
    def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile

    @property
    def path(self):
        return self.url.path

    @property
    @lru_cache(maxsize=None)
    def query(self):
        return parse_qs(self.url.query)

    @property
    @lru_cache(maxsize=None)
    def url(self):
        return urlparse(self.target)

    def body(self):
        size = self.headers.get('Content-Length')
        if not size:
            return None
        return self.rfile.read(size)

class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

class HTTPError(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


if __name__ == '__main__':
    serv = Server()
    # try:
    #     serv.serve_forever()
    # except (Exception) as error:
    #     logging("ERROR", str(error))
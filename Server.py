from http.server import SimpleHTTPRequestHandler, HTTPServer
import socketserver
import urllib.parse
import urllib.request

class Proxy(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Proxy server is running")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        url = 'https://engine.freerice.com' + parsed_path.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        req = urllib.request.Request(url, data=post_data, headers=self.headers, method='POST')
        with urllib.request.urlopen(req) as response:
            self.send_response(response.getcode())
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            self.wfile.write(response.read())

    def do_PATCH(self):
        parsed_path = urllib.parse.urlparse(self.path)
        url = 'https://engine.freerice.com' + parsed_path.path
        content_length = int(self.headers['Content-Length'])
        patch_data = self.rfile.read(content_length)

        req = urllib.request.Request(url, data=patch_data, headers=self.headers, method='PATCH')
        with urllib.request.urlopen(req) as response:
            self.send_response(response.getcode())
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            self.wfile.write(response.read())

def run(server_class=HTTPServer, handler_class=Proxy, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting proxy server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

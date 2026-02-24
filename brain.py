from http.server import BaseHTTPRequestHandler, HTTPServer
import json

PORT = 8050

class SafeSpaceHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print("Connection:", format % args)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self):

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
            msg = data.get("message","").lower()

            if "name" in msg:
                reply = "Your name is Doug. I am here."
            else:
                reply = "I hear you Doug."

        except Exception as e:
            reply = "Brain connected."

        response = json.dumps({"reply": reply}).encode()

        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(response)))
        self.end_headers()

        self.wfile.write(response)

print("SafeSpace Brain Active")
print("Listening on port", PORT)

HTTPServer(("127.0.0.1",PORT), SafeSpaceHandler).serve_forever()

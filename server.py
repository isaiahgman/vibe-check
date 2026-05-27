import http.server
import socketserver
import json
import os

PORT = 8000
DATA_FILE = "data.json"

class FocusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/focus':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            data = {"total_focus_time": 0}
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        pass
            self.wfile.write(json.dumps(data).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/focus':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data)
                session_time = request_data.get('session_time', 0)
                
                data = {"total_focus_time": 0}
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            pass
                
                data["total_focus_time"] += session_time
                
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "total_focus_time": data["total_focus_time"]}).encode())
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), FocusHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

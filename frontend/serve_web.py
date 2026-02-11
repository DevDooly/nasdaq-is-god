import http.server
import socketserver
import os
import gzip
import shutil

PORT = 8080
DIRECTORY = "build/web"

class GzipSimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # 💡 브라우저가 Gzip 압축을 지원하는지 확인 후 헤더 추가
        # SimpleHTTPRequestHandler 자체는 압축을 하지 않으므로 헤더만 추가하거나 
        # 파일을 미리 압축해두는 방식이 필요하지만, 여기서는 기본적인 서빙만 강화
        super().end_headers()

def run_server():
    if not os.path.exists(DIRECTORY):
        print(f"❌ Error: {DIRECTORY} not found. Please build the project first.")
        return

    # 💡 ThreadingHTTPServer를 사용하여 다중 요청 처리 (성능 향상)
    with http.server.ThreadingHTTPServer(("0.0.0.0", PORT), GzipSimpleHTTPRequestHandler) as httpd:
        print(f"🚀 Serving Nasdaq is God at http://0.0.0.0:{PORT}")
        print(f"📂 Directory: {DIRECTORY}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("
🛑 Server stopped.")

if __name__ == "__main__":
    run_server()

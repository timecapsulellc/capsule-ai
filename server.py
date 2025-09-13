#!/usr/bin/env python3
"""
Simple HTTP server for Capsule AI landing page preview
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import unquote
import mimetypes

class CapsuleAIServer(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP server for Capsule AI landing page"""

    def do_GET(self):
        """Handle GET requests"""
        # Decode URL
        path = unquote(self.path)

        # Default to index.html for root path
        if path == '/':
            path = '/index.html'

        # Handle static files
        if path.startswith('/static/'):
            file_path = os.path.join(os.getcwd(), path[1:])  # Remove leading slash
        else:
            file_path = os.path.join(os.getcwd(), path[1:])  # Remove leading slash

        # Check if file exists
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Set content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()

            # Send file content
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            # File not found - serve 404 or redirect to index
            if path.startswith('/app'):
                # Redirect to the actual Capsule app
                self.send_response(302)
                self.send_header('Location', 'http://localhost:7862')
                self.end_headers()
                return

            # Serve custom 404 or redirect to index
            self.send_response(302)
            self.send_header('Location', '/index.html')
            self.end_headers()

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"🌐 [Capsule AI Server] {format % args}")

def main():
    """Main server function"""
    port = 8000

    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("🚀 Starting Capsule AI Landing Page Server")
    print("=" * 50)
    print(f"📁 Serving from: {os.getcwd()}")
    print(f"🌐 Local URL: http://localhost:{port}")
    print(f"📱 Mobile testing: http://localhost:{port} (responsive design)")
    print(f"🎨 Capsule App: http://localhost:7862 (when running)")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()

    try:
        with socketserver.TCPServer(("", port), CapsuleAIServer) as httpd:
            print("✅ Server started successfully!")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
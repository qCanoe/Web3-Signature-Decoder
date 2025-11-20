#!/usr/bin/env python3
"""
EIP712 Signature Parser Web UI Startup Script
"""

import os
import sys
import webbrowser
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from web_ui import app
    print("✅ Web UI module loaded successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required dependencies are installed")
    print("Run: pip install flask")
    sys.exit(1)

def main():
    """Main function"""
    print("🚀 Starting EIP712 Signature Parser Web UI")
    print("=" * 50)
    
    # Check if port is available
    import socket
    host = '127.0.0.1'
    port = 5000
    
    # Try to bind port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.close()
    except socket.error:
        print(f"⚠️  Port {port} is already in use, trying another port...")
        port = 5001
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.close()
        except socket.error:
            print(f"❌ Port {port} is also in use, please specify port manually")
            sys.exit(1)
    
    # Start application
    url = f"http://{host}:{port}"
    print(f"🌐 Server started at: {url}")
    print("📱 Open the above address in your browser to use the Web UI")
    print("⌨️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Auto-open browser (optional)
    try:
        webbrowser.open(url)
        print("🔍 Browser opened automatically")
    except Exception as e:
        print(f"⚠️  Unable to open browser automatically: {e}")
        print(f"   Please visit manually: {url}")
    
    # Start Flask application
    try:
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 User interrupted, shutting down server...")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
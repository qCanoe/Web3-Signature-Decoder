from flask import Blueprint, render_template, send_from_directory

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@views_bp.route('/snap/install')
def snap_install():
    """Local Snap install helper page."""
    return render_template('snap_install.html')

@views_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    # Note: In production, this should be handled by Nginx/Apache
    return send_from_directory('static', filename)


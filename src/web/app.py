import os
import sys
from flask import Flask

# Add project root to path to allow imports from src.core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.web.routes.api import api_bp, snap_bp
from src.web.routes.views import views_bp

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Register Blueprints
app.register_blueprint(views_bp)
app.register_blueprint(api_bp)
app.register_blueprint(snap_bp)

if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5001"))
    app.run(debug=debug, host=host, port=port)

"""
Flask Web Application for CVForge

Main application entry point with blueprint registration.
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template, redirect, url_for
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """
    Application factory pattern.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        Configured Flask application
    """
    # Get the project root directory (parent of web/)
    project_root = Path(__file__).parent.parent
    template_dir = project_root / 'templates' / 'web'
    static_dir = project_root / 'static'
    
    app = Flask(__name__,
                template_folder=str(template_dir),
                static_folder=str(static_dir))
    
    # Default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        UPLOAD_FOLDER=Path('uploads'),
        OUTPUT_FOLDER=Path('output'),
        CV_DATA_PATH=Path('config/cv_data.yaml'),
        SETTINGS_PATH=Path('config/settings.yaml'),
        # Server-side session configuration
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR=Path('flask_session'),
        SESSION_PERMANENT=False,
        SESSION_USE_SIGNER=True,
    )
    
    # Override with custom config
    if config:
        app.config.update(config)
    
    # Ensure directories exist
    app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
    app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)
    app.config['SESSION_FILE_DIR'].mkdir(exist_ok=True)
    
    # Initialize server-side sessions
    Session(app)
    
    # Register custom Jinja2 filters
    @app.template_filter('format_enum')
    def format_enum_filter(value):
        """Format enum values for display (e.g., SkillLevel.EXPERT -> Expert)."""
        if value is None:
            return ''
        if hasattr(value, 'value'):
            # It's an enum, get the value and capitalize
            return value.value.capitalize()
        # It's already a string
        return str(value).capitalize()
    
    # Proxy fix for deployment behind reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Register blueprints
    from web.routes.main import main_bp
    from web.routes.cv_data import cv_data_bp
    from web.routes.generate import generate_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(cv_data_bp, url_prefix='/cv')
    app.register_blueprint(generate_bp, url_prefix='/generate')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return render_template('errors/500.html'), 500
    
    logger.info("CVForge application initialized")
    
    return app


def main():
    """Run the development server."""
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )


if __name__ == '__main__':
    main()

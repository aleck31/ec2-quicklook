import logging
from typing import Dict
from chalice import Chalice


# Application version
APP_VERSION = '2.0'

def get_version_info() -> Dict[str, str]:
    """Get version information"""
    return {'version': APP_VERSION}

# Set application name and version
app = Chalice(app_name='ec2-quicklook')
app.version = get_version_info()

# Enhanced logging configuration
app.log.setLevel(logging.DEBUG)
# Add timestamp and log level to format
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = app.log

# set Global CORS
# app.api.cors = True

# Register blueprints
from chalicelib.swagger import bp as swagger_bp
from chalicelib.product import bp as product_bp
from chalicelib.webui import bp as webui_bp

app.register_blueprint(swagger_bp, name_prefix='swagger')
app.register_blueprint(product_bp, name_prefix='product')
app.register_blueprint(webui_bp, name_prefix='webui')

# Log application startup
logger.info("EC2 Quicklook application initialized")

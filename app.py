import logging
from chalice import Chalice


# Set application name
app = Chalice(app_name='ec2-quicklook')

# Enhanced logging configuration
app.log.setLevel(logging.WARNING)
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
from chalicelib.web import bp as web_bp

app.register_blueprint(swagger_bp, name_prefix='swagger')
app.register_blueprint(product_bp, name_prefix='product')
app.register_blueprint(web_bp, name_prefix='webui')

# Log application startup
logger.info("EC2 Quicklook application initialized")

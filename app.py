import logging
from pydantic import BaseModel, Field
from chalice import Chalice
from chalicelib import swagger, product, web
from chalicelib.swagger.utils import get_swagger_ui


# Set application name
app = Chalice(app_name='ec2-quicklook')

# set Global CORS
# app.api.cors = True

# Register blueprint
app.register_blueprint(swagger.bp, name_prefix='swagger')
app.register_blueprint(product.bp, name_prefix='product')
app.register_blueprint(web.bp, name_prefix='webui')

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import logging
from pydantic import BaseModel, Field
from chalice import Chalice
from chalice.app import Response, AuthResponse, NotFoundError
from chalicelib import auth, swagger, product, web
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



@app.route('/auth', methods=['POST'])
def auth_token():
    """Get Auth Token"""
    # current_request.json_body - The parsed JSON body.
    body = app.current_request.json_body
    record = auth.get_users_db().get_item(
        Key={'username': body['username']})['Item']
    jwt_token = auth.get_jwt_token(
        body['username'], body['password'], record, auth.get_auth_key())
    return {'token': jwt_token}

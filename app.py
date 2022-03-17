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
app.register_blueprint(swagger.bp)
app.register_blueprint(product.bp)
app.register_blueprint(web.bp)

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)



@app.route("/docs", methods=["GET"])
def get_doc():
    """Get Swagger UI Main Page

    Returns:
        str: text/html for Swagger UI page
    """
    html = get_swagger_ui(app)
    return Response(
        body=html, 
        status_code=200,
        headers={"Content-Type": "text/html"},
    )


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


@app.route("/favicon.ico", methods=["GET"])
def get_favicon():
    """Get favicon image"""
    icon = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="96.00025019387095" height="95.9998823165437" viewBox="0 0 96.00025019387095 95.9998823165437" fill="none"><path id="分组 1" fill-rule="evenodd" style="fill:#F48D0C" transform="translate(0 0)  rotate(0 48.00012509693548 47.99994115827185)" opacity="1" d="M81.9445 81.9371C93.8445 70.0371 98.1845 53.4371 94.9745 38.1071C89.2645 38.3771 83.6445 40.6871 79.2845 45.0471L31.3145 93.0171C48.3545 99.3171 68.2545 95.6271 81.9445 81.9371Z M50.95 16.72C55.31 12.36 57.62 6.73 57.89 1.02C42.56 -2.19 25.96 2.16 14.06 14.06C0.37 27.75 -3.32 47.65 2.98 64.69L50.95 16.72Z M14.0565 81.945C17.1465 85.025 20.5465 87.605 24.1665 89.675L76.6365 37.205C81.5565 32.275 81.5565 24.295 76.6365 19.365C71.7065 14.445 63.7265 14.445 58.7965 19.365L6.32652 71.845C8.39652 75.455 10.9765 78.855 14.0565 81.945Z " /></svg>'
    return Response(
        body=icon, 
        status_code=200,
        headers={"Content-Type": "image/svg+xml"},
    )

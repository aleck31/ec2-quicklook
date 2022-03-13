import logging
from chalice import Chalice, AuthResponse, NotFoundError
from chalice.app import Response
from chalicelib import auth, swagger, product


# Set application name
app = Chalice(app_name='ec2-quicklook')

# Register blueprint
# app.register_blueprint(swagger.bp)
app.register_blueprint(product.bp)

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)



@app.route('/login', methods=['POST'])
def login():
    body = app.current_request.json_body
    dbrecord = auth.get_users_db().get_item(
        Key={'username': body['username']}
    )['Item']
    jwt_token = auth.get_jwt_token(
        body['username'], 
        body['password'], 
        dbrecord, 
        auth.get_auth_key())
    return {'token': jwt_token}


@app.route('/status', methods=['GET'])
def get_volume_detail():

    return {
        'server':'running'
    }


@app.route("/", methods=["GET"])
def get_doc():
    """Get Swagger UI Main Page

    Returns:
        str: text/html for Swagger UI page
    """
    html = swagger.get_swagger_ui(app)
    return Response(body=html, status_code=200,
                    headers={"Content-Type": "text/html"},)


# Here are a few more examples:
#
@app.route('/hello/{name}')
def hello_name(name):
    # '/hello/james' -> {"hello": "james"}
    return {'hello': name}

@app.route('/users', methods=['POST'])
def create_user():
    # This is the JSON body the user sent in their POST request.
    user_as_json = app.current_request.json_body
    # We'll echo the json body back to the user in a 'user' key.
    return {'user': user_as_json}

# See the README documentation for more examples.
#

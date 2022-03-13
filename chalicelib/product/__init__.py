import boto3
from chalice import Blueprint, AuthResponse, NotFoundError
from chalice.app import Response
from chalicelib import auth, boto_sdk
from chalicelib.utils.file import get_static_file
from chalicelib.swagger.utils import export_api_to_json
import logging


bp = Blueprint(__name__)

# Get logger
logger = logging.getLogger()


_PRICING_CLIENT = None


@bp.authorizer()
def jwt_auth(auth_request):
    token = auth_request.token
    decoded = auth.decode_jwt_token(token, auth.get_auth_key())
    return AuthResponse(routes=['*'], principal_id=decoded['sub'])


def get_pricing_client(region = 'ap-south-1'):
    global _PRICING_CLIENT
    if _PRICING_CLIENT is None:
        _PRICING_CLIENT = boto_sdk.PricingClient(
            boto3.client('pricing', region_name=region)
        )
    return _PRICING_CLIENT


@bp.route('/product/instance', methods=['GET'], authorizer=jwt_auth)
# @bp.route('/product/instance', methods=['GET'])
def get_instance_detail():
    
    return {
        'api':'instance'
    }


@bp.route('/product/volume', methods=['GET'])
def get_volume_detail():

    return {
        'api':'volume'
    }
        


@bp.route('/parms/image', methods=['GET'])
def list_images():

    return {
        'api':'image'
    }


@bp.route('/parm/instancetype', methods=['GET'])
def lis_instance_types():

    return {
        'api':'instancetype'    
    }


@bp.route('/parm/instancefamily', methods=['GET'])
def lis_instance_family():

    return {
        'api':'instancefamily'    
    }

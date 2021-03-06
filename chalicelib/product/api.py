import boto3
from chalice.app import Response, AuthResponse, BadRequestError, NotFoundError
from chalicelib import auth, sdk
from . import bp, logger


_PRICING_CLIENT = None
_EC2_CLIENT = None


@bp.authorizer()
def jwt_auth(auth_request):
    token = auth_request.token
    decoded = auth.decode_jwt_token(token, auth.get_auth_key())
    return AuthResponse(routes=['*'], principal_id=decoded['sub'])


def get_authorized_username(current_request):
    return current_request.context['authorizer']['principalId']


def get_pricing_client(region = 'ap-south-1'):
    global _PRICING_CLIENT
    if _PRICING_CLIENT is None:
        _PRICING_CLIENT = sdk.PricingClient(
            boto3.client('pricing', region_name=region)
        )
    return _PRICING_CLIENT


def get_ec2_client(region = 'us-east-1'):
    global _EC2_CLIENT
    if _EC2_CLIENT is None:
        _EC2_CLIENT = sdk.EC2Client(
            boto3.client('ec2', region_name=region)
        )
    return _EC2_CLIENT


@bp.route('/product/instance', methods=['GET'], cors=True)
# @bp.route('/product/instance', methods=['GET'])
def get_product_instance():
    query = bp.current_request.query_params
    if not query:
        raise BadRequestError('incorrect query parameter')
    try:
        pclient = get_pricing_client() 
        resp = pclient.get_product_instance(
            region = query.get('region'), 
            instance_type = query.get('type'), 
            operation = query.get('op')
        )
        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    except Exception as ex:
        logger.error(f"Failed to get instance product info: Error: {ex}'")
        return ex


@bp.route('/product/volume', methods=['GET'], cors=True)
def get_product_volume():
    query = bp.current_request.query_params
    if not query:
        raise BadRequestError('incorrect query parameter')
    try:
        pclient = get_pricing_client()
        resp = pclient.get_product_volume(
            region = query.get('region'), 
            volume_type = query.get('type'), 
            volume_size = query.get('size')
        )        
        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    except Exception as ex:
        logger.error(f"Failed to get volume product info: Error: {ex}'")
        return ex        


@bp.route('/instance/{res}', methods=['GET'], cors=True)
def get_parm_list(res):
    query = bp.current_request.query_params
    region = query.get('region')
    #replace mainland region with HongKong region 
    region = 'ap-east-1' if region in ['cn-north-1','cn-northwest-1'] else region

    try:
        eclient = get_ec2_client( region )         
        if res == 'types':             
            resp = eclient.get_instance_types(
                architecture = query.get('arch'), 
                instance_family = query.get('family')
            )           
        elif res == 'family':
            list = eclient.list_instance_family(
                architecture = query.get('arch')
            )
            resp = list
        elif res == 'operation':        
            list = eclient.list_usage_operations()
            resp = list 
                 
        else:
            resp = {
                'error':'incorrect path parameter'
            }
            # raise BadRequestError('incorrect path parameter')
        
        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    
    except Exception as ex:
        logger.error(f"Failed to get instance '{res}: Error: {ex}'")
        return ex

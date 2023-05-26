import boto3
import ast
from chalice.app import Response, AuthResponse, BadRequestError, NotFoundError
from chalicelib import sdk, utils
from . import bp, logger


_PRICING_CLIENT = None
_EC2_CLIENT = None


def get_pricing_client(region = 'ap-south-1'):
    '''Init boto3 pricing client, set default region to ap-south-1'''
    global _PRICING_CLIENT
    if _PRICING_CLIENT is None:
        _PRICING_CLIENT = sdk.PricingClient(
            boto3.client('pricing', region_name=region)
        )
    return _PRICING_CLIENT


def get_cn_credentials():
    '''get aws GCR credentials(ak/sk) from AWS Secrets Manager'''
    secretString = boto3.client('secretsmanager').get_secret_value(
        SecretId=utils.load_env_var('SECRET_NAME')
    ).get('SecretString')
    return ast.literal_eval(secretString)


def get_ec2_client( region = 'us-east-1'):
    global _EC2_CLIENT

    if _EC2_CLIENT is not None and _EC2_CLIENT.region == region:
        return _EC2_CLIENT
    else:
        if region in ['cn-north-1','cn-northwest-1']:
            cnKeys = get_cn_credentials()
            _EC2_CLIENT = sdk.EC2Client(
                boto3.client(
                    'ec2', region_name=region,
                    aws_access_key_id=cnKeys.get('access_key'),
                    aws_secret_access_key=cnKeys.get('secret_key')
                )
            )
        else:
            _EC2_CLIENT = sdk.EC2Client(
                boto3.client('ec2', region_name=region)
            )
    return _EC2_CLIENT



@bp.route('/product/instance', methods=['GET'], cors=True)
# @bp.route('/product/instance', methods=['GET'], authorizer=jwt_auth, cors=True)
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
# @bp.route('/product/volume', methods=['GET'], authorizer=jwt_auth, cors=True)
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
# @bp.route('/instance/{res}', methods=['GET'], authorizer=jwt_auth, cors=True)
def get_parm_list(res):
    query = bp.current_request.query_params

    try:
        eclient = get_ec2_client( query.get('region') )
        # /instance/types?region=xx&arch=xx&family=xx 
        if res == 'types':             
            resp = eclient.get_instance_types(
                architecture = query.get('arch'), 
                instance_family = query.get('family')
            )
        # /instance/family?region=xx&arch=xx  
        elif res == 'family':
            resp = eclient.list_instance_family(
                architecture = query.get('arch')
            )
        # /instance/detail?region=xx&type=xx 
        elif res == 'detail':
            resp = eclient.get_instance_detail(
                instance_type = query.get('type')
            )
        # /instance/operation?region=xx
        elif res == 'operation':        
            resp = eclient.list_usage_operations()                 
        else:
            # resp = {
            #     'error':'incorrect path parameter'
            # }
            raise BadRequestError('incorrect path parameter')
        
        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    
    except Exception as ex:
        logger.error(f"Failed to get instance '{res}: Error: {ex}'")
        return Response(
            body={res:str(ex)},
            status_code=400
        )

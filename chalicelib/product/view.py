import boto3
import ast
import os
from functools import lru_cache
from chalicelib.sdk import PricingClient, EC2Client
from chalice.app import Response, BadRequestError
from app import logger
from . import bp


_PRICING_CLIENT = None
_EC2_CLIENT = None

class ClientError(Exception):
    """Base exception for Client-specific errors"""
    def __init__(self, message: str, error_code: str = "CLIENT_ERROR"):
        super().__init__(message, status_code=400, error_code=error_code)
        logger.warning(f"Client error occurred: {error_code} - {message}")


@lru_cache(maxsize=128)
def get_pricing_client(region: str = 'ap-south-1') -> PricingClient:
    """
    Get cached pricing client instance form ap-south-1 endpoint
    """
    global _PRICING_CLIENT
    if _PRICING_CLIENT is None:
        logger.debug(f"Initializing new pricing client for region: {region}")
        _PRICING_CLIENT = PricingClient(
            boto3.client('pricing', region_name=region)
        )
    return _PRICING_CLIENT


def get_cn_credentials():
    """Get AWS China region credentials from Secrets Manager"""
    try:
        secret_id = os.environ.get('SECRET_NAME')
        if not secret_id:
            logger.error("SECRET_NAME environment variable not set")
            raise ValueError("SECRET_NAME environment variable not set")
            
        client = boto3.client('secretsmanager')
        secret = client.get_secret_value(SecretId=secret_id)
        secret_string = secret.get('SecretString')
        if not secret_string:
            logger.error("Empty secret value retrieved from Secrets Manager")
            raise ValueError("Empty secret value")
            
        return ast.literal_eval(secret_string)
    except Exception as e:
        logger.error(f"Failed to get China region credentials: {str(e)}")
        raise ClientError("Failed to access China region credentials")


@lru_cache(maxsize=128)
def get_ec2_client(region: str = 'ap-southeast-1') -> EC2Client:
    """Get cached EC2 client instance"""
    global _EC2_CLIENT

    if _EC2_CLIENT is not None and _EC2_CLIENT.region == region:
        logger.debug(f"Using cached EC2 client for region: {region}")
        return _EC2_CLIENT
    else:
        try:
            logger.debug(f"Initializing new EC2 client for region: {region}")
            if region in ['cn-north-1', 'cn-northwest-1']:
                cn_keys = get_cn_credentials()
                _EC2_CLIENT = EC2Client(
                        boto3.client(
                        'ec2', region_name=region,
                        aws_access_key_id=cn_keys.get('access_key'),
                        aws_secret_access_key=cn_keys.get('secret_key')
                    )
                )
            else:
                _EC2_CLIENT = EC2Client(
                    boto3.client('ec2', region_name=region)
                )
        except Exception as e:
            logger.error(f"Failed to initialize EC2 client: {str(e)}")
            raise ClientError("Failed to initialize EC2 service")
        return _EC2_CLIENT


@bp.route('/product/instance', methods=['GET'], cors=True, authorizer=None)
def get_product_instance():
    """Get EC2 instance product information"""
    query = bp.current_request.query_params    
    if not query:
        logger.warning("Missing query parameters for product instance request")
        raise BadRequestError('Incorrect query parameter')
    
    try:
        logger.debug(f"Getting product instance info for region: {query.get('region')}, type: {query.get('type')}")
        pclient = get_pricing_client()
        resp = pclient.get_product_instance(
            region=query['region'],
            instance_type=query['type'],
            operation=query['op']
        )
        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    except Exception as ex:
        logger.error(f"Failed to get instance product data: {str(ex)}")
        raise ClientError(str(ex))


@bp.route('/product/volume', methods=['GET'], cors=True, authorizer=None)
def get_product_volume():
    """Get EBS volume product information"""
    query = bp.current_request.query_params
    if not query:
        logger.warning("Missing query parameters for product volume request")
        raise BadRequestError('Incorrect query parameter')
     
    try:
        logger.debug(f"Getting product volume info for region: {query.get('region')}, type: {query.get('type')}")
        pclient = get_pricing_client()
        resp = pclient.get_product_volume(
            region=query['region'],
            volume_type=query['type'],
            volume_size=query['size']
        )
        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    except Exception as ex:
        logger.error(f"Failed to get volume product info: {str(ex)}")
        raise ClientError(str(ex))


@bp.route('/instance/{res}', methods=['GET'], cors=True, authorizer=None)
def get_param_list(res: str):
    """Get EC2 instance parameters"""
    query = bp.current_request.query_params or {}
    if not query:
        logger.warning(f"Missing query parameters for instance {res} request")
        raise BadRequestError('incorrect query parameter')  
      
    try:
        logger.debug(f"Getting instance {res} for region: {query.get('region')}")
        eclient = get_ec2_client(query.get('region'))
        
        # /instance/types?region=xx&arch=xx&family=xx
        if res == 'types':
            resp = eclient.get_instance_types(
                architecture=query['arch'],
                instance_family=query.get('family', 'all')
            )
        # /instance/family?region=xx&arch=xx
        elif res == 'family':
            resp = eclient.list_instance_family(
                architecture=query['arch']
            )
        # /instance/detail?region=xx&type=xx
        elif res == 'detail':
            resp = eclient.get_instance_detail(
                instance_type=query['type']
            )
        # /instance/operation?region=xx
        elif res == 'operation':
            resp = eclient.list_usage_operations()
        else:
            logger.error(f"Invalid resource type requested: {res}")
            raise ClientError(
                f"Invalid resource type: {res}",
                error_code="INVALID_RESOURCE"
            )

        return Response(
            body=resp,
            headers={"Content-Type": "application/json"}
        )
    
    except ClientError:
        raise
    except Exception as ex:
        logger.error(f"Failed to get instance '{res}': {str(ex)}")
        raise ClientError(str(ex))

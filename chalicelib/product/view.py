import boto3
import ast
import os
from datetime import datetime, timedelta
from typing import Dict
from chalicelib.sdk import PricingClient, EC2Client
from chalicelib.models import (
    AWSServiceError, EC2ServiceError, PricingServiceError,
    InstanceProductParams, VolumeProductParams
)
from chalice.app import Response, BadRequestError
from chalicelib.webui.view import list_ec2_regions
from app import logger
from . import bp


_PRICING_CLIENT = None
_EC2_CLIENT = None

def get_cache_headers(max_age: int = 3600) -> Dict[str, str]:
    """Generate cache control headers with specified max age"""
    expires = datetime.now() + timedelta(seconds=max_age)
    return {
        'Cache-Control': f'public, max-age={max_age}',
        'Expires': expires.strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'Content-Type': 'application/json'
    }


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


def get_cn_credentials() -> Dict[str, str]:
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
        raise AWSServiceError("Failed to access China region credentials")


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
            raise EC2ServiceError("Failed to initialize EC2 service")
        return _EC2_CLIENT


@bp.route('/product/instance', methods=['GET'], cors=True, authorizer=None)
def get_product_instance() -> Response:
    """Get EC2 instance product information"""
    query = bp.current_request.query_params    
    if not query:
        logger.warning("Missing query parameters for product instance request")
        raise BadRequestError('Incorrect query parameter')
    
    try:
        pclient = get_pricing_client()
        # Only include required parameters
        params: InstanceProductParams = {
            'region': query['region'],
            'typesize': query['typesize'],
            'op': query['op']
        }
        logger.debug(f"Getting product instance usging params: {params}")
        # Only add optional parameters if they have non-empty values
        if query.get('option'):
            params['option'] = query['option']
        if query.get('tenancy'):
            params['tenancy'] = query['tenancy']
            
        resp = pclient.get_product_instance(params)
        return Response(
            body=resp,
            headers=get_cache_headers()
        )
    except (EC2ServiceError, PricingServiceError) as ex:
        status_code = 400 if ex.error_code in ['INVALID_PARAMS', 'NOT_FOUND'] else 500
        return Response(
            body={'error': ex.service, 'message': str(ex), 'code': ex.error_code},
            status_code=status_code,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as ex:
        logger.error(f"Unexpected error: {str(ex)}")
        return Response(
            body={'error': 'InternalServerError', 'message': str(ex)},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )


@bp.route('/product/volume', methods=['GET'], cors=True, authorizer=None)
def get_product_volume() -> Response:
    """Get EBS volume product information"""
    query = bp.current_request.query_params
    if not query:
        logger.warning("Missing query parameters for product volume request")
        raise BadRequestError('Incorrect query parameter')
     
    try:
        logger.debug(f"Getting product volume info for region: {query.get('region')}, type: {query.get('type')}")
        pclient = get_pricing_client()
        # Only include required parameters
        params: VolumeProductParams = {
            'region': query['region'],
            'type': query['type'],
            'size': query['size']
        }
        # Only add optional parameters if they have non-empty values
        if query.get('option'):
            params['option'] = query['option']
            
        resp = pclient.get_product_volume(params)
        return Response(
            body=resp,
            headers=get_cache_headers()
        )
    except (EC2ServiceError, PricingServiceError) as ex:
        status_code = 400 if ex.error_code in ['INVALID_PARAMS', 'NOT_FOUND'] else 500
        return Response(
            body={'error': ex.service, 'message': str(ex), 'code': ex.error_code},
            status_code=status_code,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as ex:
        logger.error(f"Unexpected error: {str(ex)}")
        return Response(
            body={'error': 'InternalServerError', 'message': str(ex)},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )


@bp.route('/instance/{res}', methods=['GET'], cors=True, authorizer=None)
def get_param_list(res: str) -> Response:
    """Get EC2 instance parameters"""
    query = bp.current_request.query_params or {}
    
    try:
        # Handle endpoints using pattern matching
        match res:
            # Endpoints that don't require query parameters
            case 'regions':
                resp = list_ec2_regions()
            case 'operations':
                eclient = get_ec2_client('us-east-1')  # Default region for operations
                resp = eclient.list_usage_operations()
            case 'categories':
                eclient = get_ec2_client('us-east-1')  # Default region for categories
                resp = eclient.list_instance_categories()
            case 'voltypes':
                pclient = get_pricing_client()
                resp = pclient.get_attribute_values(
                    service_code='AmazonEC2',
                    attribute_name='volumeApiName'
                ).get('data', [])
                # Remove unsupported volume types
                resp = [v for v in resp if v not in ['sc1', 'st1']]

            # Endpoints that require query parameters
            case 'family' | 'sizes' | 'detail':
                if not query:
                    logger.warning(f"Missing query parameters for instance {res} request")
                    raise BadRequestError('incorrect query parameter')

                logger.debug(f"Getting instance {res} for region: {query.get('region')}")
                eclient = get_ec2_client(query.get('region'))
                
                match res:
                    case 'family':  # /instance/family?region=xx&arch=xx&category=xx
                        resp = eclient.list_instance_family(
                            architecture=query['arch']
                        )
                        # Filter by category if provided
                        if query.get('category'):
                            resp = [f for f in resp if f['category'] == query['category']]
                    case 'sizes':  # /instance/sizes?region=xx&arch=xx&family=xx
                        resp = eclient.get_instance_sizes(
                            architecture=query['arch'],
                            instance_type=query.get('family', 'all')
                        )
                    case 'detail':  # /instance/detail?region=xx&type=xx
                        resp = eclient.get_instance_detail(
                            instance_type=query['type']
                        )

            case _:
                logger.error(f"Invalid resource type requested: {res}")
                raise EC2ServiceError(
                    f"Invalid resource type: {res}",
                    error_code="INVALID_RESOURCE"
                )

        # Use longer cache duration (24 hours) for relatively static data
        max_age = 86400 if res in ['regions', 'operations', 'categories', 'voltypes', 'sizes', 'detail'] else 3600
        return Response(
            body=resp,
            headers=get_cache_headers(max_age)
        )
    
    except (EC2ServiceError, PricingServiceError) as ex:
        status_code = 400 if ex.error_code in ['INVALID_PARAMS', 'NOT_FOUND'] else 500
        return Response(
            body={'error': ex.service, 'message': str(ex), 'code': ex.error_code},
            status_code=status_code,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as ex:
        logger.error(f"Unexpected error: {str(ex)}")
        return Response(
            body={'error': 'InternalServerError', 'message': str(ex)},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

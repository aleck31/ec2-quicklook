import ast
import time
from functools import lru_cache, wraps
import boto3
from typing import Dict, List, Any, Callable, TypeVar, cast
from chalicelib.config import load_config
from chalicelib.models import (
    EC2ServiceError, PricingServiceError,
    ProductResponse, InstanceProductParams, VolumeProductParams
)
from app import logger


# Define EC2 Product Page URLs
INSTANCE_TYPE_URL = 'https://aws.amazon.com/cn/ec2/instance-types/'
VOLUME_TYPE_URL = 'https://aws.amazon.com/cn/ebs/volume-types/'

# Define a generic type for the function
T = TypeVar('T')

def timed_lru_cache(seconds: int, maxsize: int = 128):
    """LRU Cache decorator with timeout
    
    Args:
        seconds: Number of seconds to keep entries in cache
        maxsize: Maximum cache size (default: 128)
        
    Returns:
        Decorated function with timed cache
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create cache with timeout
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = seconds
        func.expiration = time.time() + seconds
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if time.time() > func.expiration:
                func.cache_clear()
                func.expiration = time.time() + func.lifetime
                logger.debug(f"Cache cleared for {func.__name__} due to expiration")
            return func(*args, **kwargs)
        
        wrapper.cache_info = func.cache_info
        wrapper.cache_clear = func.cache_clear
        return cast(Callable[..., T], wrapper)
    
    return decorator


class EC2Client:
    """Client for EC2-related operations"""
    def __init__(self, boto3_client: boto3.client) -> None:
        self._boto3_client = boto3_client
        self.region = boto3_client._client_config.region_name
        logger.debug(f"Initialized EC2Client for region: {self.region}")

    @timed_lru_cache(seconds=86400, maxsize=128)  # Cache for 24 hours since this rarely changes
    def list_usage_operations(self) -> Dict[str, Any]:
        """List EC2 usage operations with caching"""
        try:
            return load_config('operation')
        except Exception as ex:
            logger.error(f"Failed to load operations config: {str(ex)}")
            raise EC2ServiceError(f"Failed to load operations config: {str(ex)}")

    @timed_lru_cache(seconds=86400, maxsize=128)  # Cache for 24 hours since categories rarely change
    def list_instance_categories(self) -> List[Dict[str, Any]]:
        """List EC2 instance categories"""
        try:
            instance_list = load_config('instance')
            categories = {}
            
            for family in instance_list:
                if family['category'] not in categories:
                    categories[family['category']] = {
                        'category': family['category'],
                        'description': family['description'],
                        'display_name': family['display_name']
                    }
            
            return list(categories.values())
        except Exception as ex:
            logger.error(f"Failed to load instance categories: {str(ex)}")
            raise EC2ServiceError(f"Failed to load instance categories: {str(ex)}")

    @timed_lru_cache(seconds=86400, maxsize=128)  # Cache for 24 hours since families rarely change
    def list_instance_family(self, architecture: str) -> List[Dict[str, Any]]:
        """List EC2 instance families"""
        try:
            logger.debug(f"Cache info before: {self.list_instance_family.cache_info()}")
            instance_list = load_config('instance')
            
            family_list = []            
            for family in instance_list:
                for instance in family['family']:
                    if instance['architecture'] == architecture:
                        family_list.append({
                            'category': family['category'],
                            'name': instance['name'],
                            'note': instance['note'],
                            'architecture': instance['architecture']
                        })

            logger.debug(f"Filtered family list for {architecture}: {len(family_list)}")
            return family_list
        except Exception as ex:
            logger.error(f"Failed to load instance families: {str(ex)}")
            raise EC2ServiceError(f"Failed to load instance families: {str(ex)}")

    @timed_lru_cache(seconds=3600, maxsize=256)
    def get_instance_sizes(self, architecture: str, instance_type: str) -> List[Dict[str, str]]:
        """Get available EC2 instance sizes with enhanced caching and pagination
        
        Args:
            architecture: The processor architecture (e.g., 'x86_64', 'arm64')
            instance_type: The instance type/family (e.g., 'm5', 't3') or 'all'
            
        Returns:
            List of instance types with their type/family names
            
        Raises:
            EC2ServiceError: If the API call fails
        """
        try:
            # Start time for performance tracking
            start_time = time.time()
            
            # Optimize filters for better performance
            filters = [
                {'Name': 'current-generation', 'Values': ['true']},
                {'Name': 'processor-info.supported-architecture', 'Values': [architecture]}
            ]            
            if instance_type != 'all':
                filters.append({
                    'Name': 'instance-type', 'Values': [f"{instance_type}.*"]
                })

            instance_sizes = []

            # Use paginator instead of manual pagination for better efficiency
            paginator = self._boto3_client.get_paginator('describe_instance_types')
            page_iterator = paginator.paginate(
                Filters=filters,
                # Use PaginationConfig to limit page size for more responsive results
                PaginationConfig={'PageSize': 100}
            )

            # Process pages more efficiently
            for page in page_iterator:
                for i in page['InstanceTypes']:
                    # Extract only the fields we need (data minimization)
                    insType = i['InstanceType']
                    instance_sizes.append({
                        'instanceType': insType,
                        'instanceFamily': insType.split('.')[0]
                    })
            
            # Sort results for consistent ordering
            instance_sizes.sort(key=lambda x: x['instanceType'])

            # Log performance metrics
            elapsed_time = time.time() - start_time
            logger.debug(f"Found {len(instance_sizes)} available sizes for the {instance_type} instance type in {elapsed_time:.2f}s")

            return instance_sizes

        except Exception as ex:
            logger.error(f"Failed to get instance types: {str(ex)}")
            if isinstance(ex, boto3.exceptions.Boto3Error):
                raise EC2ServiceError(str(ex), error_code=ex.__class__.__name__)
            raise EC2ServiceError(f"Failed to get instance types: {str(ex)}")

    @timed_lru_cache(seconds=3600, maxsize=128)  # Cache for 1 hour since details may change
    def get_instance_detail(self, instance_type: str) -> Dict[str, Any]:
        """Get detailed information about an EC2 instance type"""
        try:
            resp = self._boto3_client.describe_instance_types(
                InstanceTypes=[instance_type]
            )
            instances = resp.get('InstanceTypes', [])
            
            if not instances:
                logger.warning(f"Instance type not found: {instance_type}")
                raise EC2ServiceError(f"Instance type {instance_type} not found", error_code="NOT_FOUND")
                
            return instances[0]

        except Exception as ex:
            logger.error(f"Failed to get instance details: {str(ex)}")
            if isinstance(ex, boto3.exceptions.Boto3Error):
                raise EC2ServiceError(str(ex), error_code=ex.__class__.__name__)
            raise EC2ServiceError(f"Failed to get instance details: {str(ex)}")


class PricingClient:
    """Client for AWS Pricing operations"""
    def __init__(self, boto3_client) -> None:
        self._boto3_client = boto3_client
        logger.debug("Initialized PricingClient")

    #SDK: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/pricing.html#Pricing.Client.describe_services
    @timed_lru_cache(seconds=86400, maxsize=128)  # Cache for 24 hours since service codes rarely change
    def get_service_codes(self) -> Dict[str, Any]:
        """Get AWS service codes with caching"""
        try:
            logger.debug("Retrieving AWS service codes")
            service_codes = []
            describe_args = {}
            while True:
                describe_result = self._boto3_client.describe_services(
                    **describe_args,
                    # FormatVersion='string',
                    # NextToken='string',
                    # MaxResults=100
                )
                service_codes.extend(
                    [s['ServiceCode'] for s in describe_result['Services']]
                )
                if 'NextToken' not in describe_result:
                    break
                describe_args['NextToken'] = describe_result['NextToken']
            
            logger.debug(f"Found {len(service_codes)} service codes")
            return {
                'count': len(service_codes),
                'data': service_codes
            }
        except Exception as ex:
            logger.error(f"Failed to get service codes: {str(ex)}")
            raise PricingServiceError(f"Failed to get service codes: {str(ex)}")

    @timed_lru_cache(seconds=86400, maxsize=128)  # Cache for 24 hours since attributes rarely change
    def get_service_attributes(self, service_code: str = 'AmazonEC2') -> Dict[str, Any]:
        """Get service attributes with caching"""
        try:
            resp = self._boto3_client.describe_services(
                ServiceCode=service_code
            )
            services = resp.get('Services', [])
            
            if not services:
                logger.warning(f"Service not found: {service_code}")
                raise PricingServiceError(f"Service {service_code} not found")
                
            attributes = services[0].get('AttributeNames', [])
            return {
                'count': len(attributes),
                'data': attributes
            }
        except Exception as ex:
            logger.error(f"Failed to get service attributes: {str(ex)}")
            raise PricingServiceError(f"Failed to get service attributes: {str(ex)}")

    @timed_lru_cache(seconds=86400, maxsize=128)  # Cache for 24 hours since values rarely change
    def get_attribute_values(
        self,
        service_code: str = 'AmazonEC2',
        attribute_name: str = 'instanceType'
    ) -> Dict[str, Any]:
        """Get attribute values with caching"""
        try:
            values = []
            describe_args = {
                    'ServiceCode' : service_code,
                    'AttributeName' : attribute_name,
            }
            while True:        
                response = self._boto3_client.get_attribute_values(
                    **describe_args
                )
                values.extend(
                    [a['Value'] for a in response['AttributeValues']]
                )
                if 'NextToken' not in response:
                    break
                describe_args['NextToken'] = response['NextToken']
            
            return {
                'count': len(values),
                'data': values
            }
        
        except Exception as ex:
            logger.error(f"Failed to get attribute values: {str(ex)}")
            raise PricingServiceError(f"Failed to get attribute values: {str(ex)}")

    def get_product_instance(self, params: InstanceProductParams) -> ProductResponse:
        """Get EC2 instance Attributes and ListPrice [unit: Month]"""
        try:
            # Build required filters
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'locationType', 'Value': 'AWS Region'},
                {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonEC2'},
                # {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Compute Instance'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus','Value': 'UnusedCapacityReservation'}, 
                {'Type': 'TERM_MATCH', 'Field': 'RegionCode', 'Value': params['region']},
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': params['typesize']},
                {'Type': 'TERM_MATCH', 'Field': 'operation', 'Value': params['op']},
                # {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                # {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'marketoption','Value': params.get('option', 'OnDemand')},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': params.get('tenancy', 'Shared')}
            ]

            result = self._boto3_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters
            )

            price_list = result.get('PriceList', [])
            if len(price_list) != 1:
                logger.warning("Invalid parameter combination for product instance")
                raise PricingServiceError('Invalid parameter combination', error_code="INVALID_PARAMS")

            # Convert the string to a dictionary using ast.literal_eval()
            result_dict = ast.literal_eval(price_list[0])
            attributes = result_dict['product']['attributes']
            
            # Extract and organize product information
            product_info = {
                'productMeta': {
                    'instanceFamily': attributes['instanceFamily'],
                    'currentGeneration': attributes['currentGeneration'],
                    'introduceUrl': f"{INSTANCE_TYPE_URL}{params['typesize'].split('.')[0]}",
                    'regionCode': attributes['regionCode'],
                    'location': attributes['location'],
                    'tenancy': attributes['tenancy'],
                    'capacitystatus': attributes['capacitystatus'],
                    'usagetype': attributes['usagetype'],
                    'instancesku': attributes['instancesku'],
                    'operation': attributes['operation'],
                    'normalizationSizeFactor': attributes['normalizationSizeFactor'],
                    'ecu': attributes['ecu'],
                },
                'hardwareSpecs': {
                    'physicalProcessor': attributes['physicalProcessor'],
                    'clockSpeed': attributes.get('clockSpeed'),
                    'processorArchitecture': attributes['processorArchitecture'],
                    'vcpu': attributes['vcpu'],
                    'memory': attributes['memory'],
                    'dedicatedEbsThroughput': attributes['dedicatedEbsThroughput'],
                    'networkPerformance': attributes['networkPerformance'],
                    'gpu': attributes.get('gpu')
                },
                'softwareSpecs': {
                    'operatingSystem': attributes['operatingSystem'],
                    'preInstalledSw': attributes['preInstalledSw'],
                    'licenseModel': attributes['licenseModel'],
                },
                'instanceStorage': {
                    'volumeType': 'Instance Store',
                    'description': attributes['storage']
                },
                'productFeature': {
                    'intelTurboAvailable': attributes['intelTurboAvailable'],
                    'vpcnetworkingsupport': attributes['vpcnetworkingsupport'],
                    'enhancedNetworkingSupported': attributes['enhancedNetworkingSupported'],
                    'classicnetworkingsupport': attributes['classicnetworkingsupport'],
                    'intelAvx2Available': attributes['intelAvx2Available'],
                    'intelAvxAvailable': attributes['intelAvxAvailable'],
                    'processorFeatures': attributes.get('processorFeatures'),
                }
            }

            # Extract and calculate pricing information
            option_type = params.get('option', 'OnDemand')
            terms_dict = result_dict.get('terms', {}).get(option_type, {})
            if not terms_dict:
                raise PricingServiceError(f"No pricing terms found for option: {option_type}", error_code="INVALID_OPTION")
            terms = next(iter(terms_dict.values()))
            price_dimensions = terms['priceDimensions']
            price_info = next(iter(price_dimensions.values()))
            # Extract unit price and currency
            currency = next(iter(price_info['pricePerUnit']))
            value = float(price_info['pricePerUnit'].get(currency))
            
            # Calculate monthly price (730 hours)
            price_info.update({
                'unit': 'Month',
                'pricePerUnit': {
                    'currency': currency,
                    'value': value * 730
                },
                'effectiveDate': terms['effectiveDate']
            })

            product_info['listPrice'] = price_info
            return product_info

        except Exception as ex:
            logger.error(f"Failed to get instance product data: {str(ex)}")
            if isinstance(ex, boto3.exceptions.Boto3Error):
                raise PricingServiceError(str(ex), error_code=ex.__class__.__name__)
            raise PricingServiceError(f"Failed to get instance product data: {str(ex)}")

    def get_product_volume(self, params: VolumeProductParams) -> ProductResponse:
        """Get EBS volume Attributes and ListPrice [unit: GB-Mo]"""
        try:
            # Build filters, excluding None values
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'locationType', 'Value': 'AWS Region'},
                {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonEC2'},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
                {'Type': 'TERM_MATCH', 'Field': 'RegionCode', 'Value': params['region']},
                {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': params['type']}
            ]

            result = self._boto3_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters
            )

            price_list = result.get('PriceList', [])
            if len(price_list) != 1:
                logger.warning("Invalid parameter combination for product volume")
                raise PricingServiceError('Invalid parameter combination', error_code="INVALID_PARAMS")

            result_dict = ast.literal_eval(price_list[0])
            attributes = result_dict['product']['attributes']

            # Extract and organize product information
            product_info = {
                'productMeta': {
                    'volumeType': attributes['volumeType'],
                    'location': attributes['location'],
                    'storageMedia': attributes['storageMedia'],
                    'introduceUrl': f"{VOLUME_TYPE_URL}#{params['type']}",
                    'usagetype': attributes['usagetype'],
                },
                'productSpecs': {
                    'maxThroughputvolume': attributes['maxThroughputvolume'],
                    'maxIopsvolume': attributes.get('maxIopsvolume'),
                    'maxVolumeSize': attributes.get('maxVolumeSize'),
                    'maxIopsBurstPerformance': attributes.get('maxIopsBurstPerformance'),
                }
            }

            # Extract and calculate pricing information
            option_type = params.get('option', 'OnDemand')
            terms_dict = result_dict.get('terms', {}).get(option_type, {})
            if not terms_dict:
                raise PricingServiceError(f"No pricing terms found for option: {option_type}", error_code="INVALID_OPTION")
            terms = next(iter(terms_dict.values()))
            price_dimensions = terms['priceDimensions']
            price_info = next(iter(price_dimensions.values()))
            
            currency = next(iter(price_info['pricePerUnit']))
            value = float(price_info['pricePerUnit'].get(currency))
            
            # Calculate price for specified volume size
            price_info.update({
                'unit': 'Month',
                'pricePerUnit': {
                    'currency': currency,
                    'value': value * float(params['size'])
                },
                'effectiveDate': terms['effectiveDate']
            })

            product_info['listPrice'] = price_info
            return product_info

        except Exception as ex:
            logger.error(f"Failed to get volume product data: {str(ex)}")
            if isinstance(ex, boto3.exceptions.Boto3Error):
                raise PricingServiceError(str(ex), error_code=ex.__class__.__name__)
            raise PricingServiceError(f"Failed to get volume product data: {str(ex)}")

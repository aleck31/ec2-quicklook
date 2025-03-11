import os
import boto3
from typing import Dict, Any
from chalice.app import BadRequestError
from app import logger


_CONF_DB = None


def get_conf_db():
    """Get DynamoDB table resource for configuration
    
    Returns:
        DynamoDB table resource
        
    Note:
        Uses environment variables:
        - AWS_REGION: Runtime region
        - APP_TABLE_NAME: DynamoDB table name
    """
    global _CONF_DB
    if _CONF_DB is None:
        # get runtime region from reserved env var
        try:
            runtime_region = os.environ['AWS_REGION']
        except KeyError:
            # set to dynamodb region for local test
            runtime_region = 'ap-southeast-1'
        # load ddb tablename from lambda env var
        try:
            table_name = os.environ['APP_TABLE_NAME']
        except KeyError:
            raise RuntimeError("APP_TABLE_NAME environment variable not set")
            
        _CONF_DB = boto3.resource('dynamodb', region_name=runtime_region).Table(table_name)
    return _CONF_DB


def load_config(name: str) -> Dict[str, Any]:
    """Load config by name from DynamoDB table
    
    Args:
        name: Configuration name to load
        
    Returns:
        Dict containing configuration values
        
    Raises:
        BadRequestError: If configuration cannot be loaded
    """
    try:
        response = get_conf_db().get_item(Key={'name': name})
        if 'Item' not in response:
            raise KeyError(f"Configuration '{name}' not found")
        return response['Item']['config']
    except Exception as ex:
        logger.error(f"Failed to load config '{name}': {str(ex)}")
        raise BadRequestError(str(ex))


def get_version(name: str) -> str:
    """Get version from DynamoDB table
    
    Args:
        name: Name of component to get version for
        
    Returns:
        Version string, defaults to '0.0' if not found
    """
    try:
        response = get_conf_db().get_item(Key={'name': name})
        if 'Item' not in response:
            logger.warning(f"Version for '{name}' not found, using default")
            return '0.0'
        return response['Item']['version']
    except Exception as ex:
        logger.error(f"Failed to get version from database: {str(ex)}")
        return '0.0'

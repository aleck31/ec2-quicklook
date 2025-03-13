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
        logger.debug(f"Connected to DDB [{table_name}] in [{runtime_region}]")
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
        logger.debug(f"Loading config '{name}' from DynamoDB")
        response = get_conf_db().get_item(Key={'name': name}, ConsistentRead=True)
        if 'Item' not in response:
            raise KeyError(f"Configuration '{name}' not found")
        config = response['Item']['config']
        return config
    except Exception as ex:
        logger.error(f"Failed to load config '{name}': {str(ex)}")
        raise BadRequestError(str(ex))

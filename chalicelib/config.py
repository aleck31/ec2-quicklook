import os
import boto3
from chalice.app import BadRequestError
from app import logger


_CONF_DB = None


def get_conf_db():
    global _CONF_DB
    if _CONF_DB is None:
        # get runtime region from reserved env var
        try:
            runtime_region = os.environ['AWS_REGION']
        except Exception:
            # set to dynamodb region for local test
            runtime_region = 'ap-southeast-1'
        # load ddb tablename from lambda env var
        _CONF_DB = boto3.resource('dynamodb', region_name=runtime_region).Table(
            os.environ['APP_TABLE_NAME']
        )
    return _CONF_DB


def load_config(name):
    """Load config by name from Dynamodb table"""
    try:
        item_dict = get_conf_db().get_item(
            Key={'name': name}
        )['Item']['config']
        return item_dict
    except Exception as ex:
        logger.error(str(ex))
        raise BadRequestError(ex)
        # return str(ex)

def get_version(name):
    """Get version from Dynamodb table"""
    try:
        version = get_conf_db().get_item(
            Key={'name': name}
        )['Item']['version']
        return version
    except Exception as ex:
        logger.error(f"Failed to get version from database: {str(ex)}")
        return '0.0'
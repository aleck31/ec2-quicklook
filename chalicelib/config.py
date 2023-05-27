import os
import logging
import boto3
from chalice.app import BadRequestError


# Get logger
logger = logging.getLogger()


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
            os.environ['CONF_TABLE_NAME']
        )
    return _CONF_DB


def load_config(name):
    # load config by name from Dynamodb table
    try:
        item_dict = get_conf_db().get_item(
            Key={'name': name}
        )['Item']['config']
        return item_dict
    except Exception as ex:
        raise BadRequestError(ex)
        # return str(ex)

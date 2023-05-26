import logging
import boto3
from chalicelib.utils import load_env_var


# Get logger
logger = logging.getLogger()


_CONF_DB = None


def get_conf_db(stage='dev'):
    global _CONF_DB
    if _CONF_DB is None:
        # load ddb tablename from env config
        tableName = load_env_var('CONF_TABLE_NAME', stage)
        _CONF_DB = boto3.resource('dynamodb').Table(tableName)
    return _CONF_DB


def load_config(name):
    # load config by name from Dynamodb table
    try:
        item_dict = get_conf_db().get_item(
            Key={'name': name}
        )['Item']['config']
        return item_dict
    except Exception as ex:
        return str(ex)
    
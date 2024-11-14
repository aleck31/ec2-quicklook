import os
import json
from typing import Optional, Dict
from urllib.parse import urlencode
from chalice.app import Request
from app import logger


def load_json_file(filename: str):
    """Load example config list from json file"""    
    # usage operation config: ec2_operation.json
    # instance family config: ec2_instance.json
    if not filename.endswith('.json'):
        filename = f"{filename}.json"
    try:
        with open(os.path.join('example', filename), encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filename}")
        raise ValueError(f"Config file not found: {filename}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {filename}")
        raise ValueError(f"Invalid JSON in config file: {filename}")


def get_table_name(stage='dev'):
    '''load table name from config'''
    try:
        tableName = load_local_env_var('APP_TABLE_NAME', stage)
        logger.debug(f"Retrieved table name for stage {stage}: {tableName}")
        return tableName
    except Exception as e:
        logger.error(f"Failed to get table name for stage {stage}: {str(e)}")
        raise

CONFIG_PATH = os.path.join('.chalice', 'config.json')
    
def load_local_env_var(env_var, stage='dev'):
    '''load environment variable from .chalice config'''
    try:
        # Use chalice modules to load the config directly.
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        value = config['stages'][stage]['environment_variables'].get(env_var)
        logger.debug(f"Loaded env var {env_var} for stage {stage}")
        return value
    except Exception as e:
        logger.error(f"Failed to load env var {env_var} for stage {stage}: {str(e)}")
        raise


def write_local_env_var(key, value, stage):
    '''write environment variable to .chalice config'''
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            config['stages'].setdefault(stage, {}).setdefault(
                'environment_variables', {}
            )[key] = value
        with open(CONFIG_PATH, 'w') as f:
            serialized = json.dumps(config, indent=2, separators=(',', ': '))
            f.write(serialized + '\n')
        logger.debug(f"Successfully wrote env var {key} for stage {stage}")
    except Exception as e:
        logger.error(f"Failed to write env var {key} for stage {stage}: {str(e)}")
        raise


def remove_local_env_var(env_var, stage):
    '''remove environment variable from .chalice config'''
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            env_vars = config['stages'].get(stage).get(
                'environment_variables', {})
            for key in list(env_vars):
                if key.endswith(env_var):
                    del_value = env_vars.pop(key)
            if not env_vars:
                del config['stages'][stage]['environment_variables']
        with open(CONFIG_PATH, 'w') as f:
            serialized = json.dumps(config, indent=2, separators=(',', ': '))
            f.write(serialized + '\n')
        logger.debug(f"Successfully removed env var {env_var} for stage {stage}")
    except Exception as e:
        logger.error(f"Failed to remove env var {env_var} for stage {stage}: {str(e)}")
        raise


def exist_in_config(env_var, stage):
    '''check if environment variable exists in .chalice config'''
    try:
        with open(CONFIG_PATH) as f:
            exists = env_var in json.load(f)['stages'].get(stage, {}).get('environment_variables', {})
        logger.debug(f"Checked existence of env var {env_var} in stage {stage}")
        return exists
    except Exception as e:
        logger.error(f"Failed to check env var {env_var} existence in stage {stage}: {str(e)}")
        raise


def build_api_endpoint(
    current_request: Request, 
    request_path: str, 
    query_params: Optional[Dict] = None
) -> str:
    logger.debug(f"Building API endpoint for path: {request_path}")
    request_dict = current_request.to_dict()

    context = request_dict["context"]
    stage = context.get("stage")
    api_domain = context.get("domainName")
    api_id = context.get("apiId")

    if query_params is not None:
        if "api_id" in query_params:
            # replace api value with current api id
            query_params["api_id"] = api_id

        if "stage" in query_params:
            query_params["stage"] = stage

    if query_params is not None:
        # url = f"https://{api_domain}/{stage}/{request_path.strip('/')}/?"
        url = f"/{stage}/{request_path.strip('/')}/?" if stage is not None else f"/{request_path.strip('/')}/?"
        url = url + urlencode(query_params)
    else:
        # url = f"https://{api_domain}/{stage}/{request_path.strip('/')}"
        url = f"/{stage}/{request_path.strip('/')}" if stage is not None else f"/{request_path.strip('/')}"

    logger.debug(f"Built API endpoint: {url}")
    return url


def remove_base_path_slash(api_spec_json_dict: Dict) -> Dict:
    """Remove leading slash in basePath property
    Args:
        api_spec_json_dict (Dict): OpenAPI spec in json dictionary format

    Returns:
        Dict: json dictionary with leading slash removed from 'basePath'
    """
    try:
        for key, value in api_spec_json_dict.items():
            if key == "servers":
                servers = api_spec_json_dict["servers"]
                for i in range(len(servers)):
                    if "variables" in servers[i]:
                        variables = servers[i]["variables"]
                        if "basePath" in variables:
                            base_path = variables["basePath"]
                            if "default" in base_path:
                                default_base_path = base_path["default"]
                                # Remove leading '/' otherwise url will generate incorrect path
                                slash_stripped = default_base_path.strip("/")
                                # update json dictionary
                                api_spec_json_dict["servers"][i]["variables"]["basePath"][
                                    "default"
                                ] = slash_stripped
                                logger.debug(f"Updated base path to: {slash_stripped}")
        return api_spec_json_dict
    except Exception as e:
        logger.error(f"Failed to process API spec: {str(e)}")
        raise

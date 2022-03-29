import os
import json
import logging
from typing import Optional, Dict
from urllib.parse import urlencode
from chalice.app import Request


logger = logging.getLogger()


def load_json_config(config):
    '''load config list from json file'''
    # usage operation config: ec2_operation.json
    # instance family config: ec2_instance.json
    file_name = config+'.json'
    with open(os.path.join('chalicelib', file_name), encoding='utf-8') as f:
        config = json.load(f)
    return config['config']


def load_env_var(env_var,stage='dev'):
    '''load environment variable from .chalice config'''
    # User the chalice modules to load the config directly.
    with open(os.path.join('.chalice', 'config.json')) as f:
        config = json.load(f)
    return config['stages'][stage]['environment_variables'].get(env_var)


def write_env_var(key, value, stage):
    '''write environment variable to .chalice config'''
    with open(os.path.join('.chalice', 'config.json')) as f:
        config = json.load(f)
        config['stages'].setdefault(stage, {}).setdefault(
            'environment_variables', {}
        )[key] = value
    with open(os.path.join('.chalice', 'config.json'), 'w') as f:
        serialized = json.dumps(config, indent=2, separators=(',', ': '))
        f.write(serialized + '\n')


def remove_env_var(env_var, stage):
    '''remove environment variable from .chalice config'''
    with open(os.path.join('.chalice', 'config.json')) as f:
        config = json.load(f)
        env_vars = config['stages'].get(stage).get(
            'environment_variables', {})
        for key in list(env_vars):
            if key.endswith(env_var):
                del_value = env_vars.pop(key)
        if not env_vars:
            del config['stages'][stage]['environment_variables']
    with open(os.path.join('.chalice', 'config.json')) as f:
        serialized = json.dumps(config, indent=2, separators=(',', ': '))
        f.write(serialized + '\n')


def exist_in_config(env_var, stage):
    '''check if environment variable exists in .chalice config'''
    with open(os.path.join('.chalice', 'config.json')) as f:
        return env_var in json.load(f)['stages'].get(stage, {}).get('environment_variables', {})


def build_api_endpoint(
    current_request: Request, 
    request_path: str, 
    query_params: Optional[Dict] = None
) -> str:
    logger.info(f"Enter build_api_endpoint for {request_path}")
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

    logger.info(f"Exit build_api_endpoint: {url}")
    return url


def remove_base_path_slash(api_spec_json_dict: Dict) -> Dict:
    """Remove leading slash in basePath property

    Args:
        api_spec_json_dict (Dict): OpenAPI spec in json dictionary format

    Returns:
        Dict: json dictionary with leading slash removed from 'basePath'
    """
    for key, value in api_spec_json_dict.items():
        logger.debug(f"Json spec: {key}:{value}")
        if key == "servers":
            servers = api_spec_json_dict["servers"]
            for i in range(len(servers)):
                if "variables" in servers[i]:
                    variables = servers[i]["variables"]
                    logger.debug(f"servers[{i}]['variables'] = {variables}")
                    if "basePath" in variables:
                        base_path = variables["basePath"]
                        logger.debug(f"variables['basePath'] = {base_path}")
                        if "default" in base_path:
                            default_base_path = base_path["default"]
                            logger.debug(f"base_path['default'] = {default_base_path}")
                            # Remove leading '/' otherwise url will generate incorrect path
                            slash_stripped = default_base_path.strip("/")
                            # update json dictionary
                            api_spec_json_dict["servers"][i]["variables"]["basePath"][
                                "default"
                            ] = slash_stripped
                            logger.info(
                                f"""default base_path =
                                {api_spec_json_dict['servers'][i]
                                ['variables']['basePath']['default']}"""
                            )
    return api_spec_json_dict

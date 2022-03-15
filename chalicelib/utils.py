import os
import json



def load_json_config(config):
    '''load config list from json file'''
    # usage operation config: ec2_operation.json
    # instance family config: ec2_instance.json
    file_name = config+'.json'
    with open(os.path.join('chalicelib', file_name), encoding='utf-8') as f:
        config = json.load(f)
    return config['list']


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

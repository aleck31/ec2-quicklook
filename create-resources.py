import os
import uuid
import json
import argparse
import base64
import boto3
from chalicelib.utils import write_local_env_var, exist_in_config, load_local_env_var, load_json_file


# Define Constants
AUTH_KEY_PARAM_NAME = '/ec2-quicklook/auth-key'
TABLES = {
    'app': {
        'prefix': 'quicklook-app',
        'env_var': 'APP_TABLE_NAME',
        'hash_key': 'name'
    }
}
_BOTO3_SESSION = None


def get_session(region=None):
    """Get boto3 session"""
    global _BOTO3_SESSION
    if _BOTO3_SESSION is None:
        if region:
            _BOTO3_SESSION = boto3.Session(region_name=region)
        else:
            _BOTO3_SESSION = boto3.Session()
        print(f"Session in region: {_BOTO3_SESSION.region_name}")
    return _BOTO3_SESSION


def create_auth_key_if_needed():
    '''Create auth key if it doesn't exist'''
    session = get_session()
    client_ssm = session.client('ssm')
    try:
        resp = client_ssm.get_parameter(Name=AUTH_KEY_PARAM_NAME)
        print(f"Skipping, resource {resp['Parameter']['Name']} already exists")
        return resp['Parameter']['Name']
    except client_ssm.exceptions.ParameterNotFound:
        kms = session.client('kms')
        random_bytes = kms.generate_random(NumberOfBytes=32)['Plaintext']
        encoded_random_bytes = base64.b64encode(random_bytes).decode()
        # Save auth key to ssm parameter
        client_ssm.put_parameter(
            Name=AUTH_KEY_PARAM_NAME, 
            Value=encoded_random_bytes, 
            Type='SecureString'
        )
        print(f"Generating new auth key: {AUTH_KEY_PARAM_NAME}")
    except Exception as ex:
        print(f"Error occurred while checking/creating auth key: {str(ex)}")


def create_table(table_name_prefix, hash_key, range_key=None):
    """
    Create a DynamoDB table with the given parameters.

    Args:
        table_name_prefix (str): Prefix for the table name
        hash_key (str): Hash key for the table
        range_key (str, optional): Range key for the table. Defaults to None.

    Returns:
        str: Name of the created table, or None if creation failed
    """
    session = get_session()
    table_name = f'{table_name_prefix}-{str(uuid.uuid4())}'
    client_ddb = session.client('dynamodb')

    # Build key schema and attribute definitions
    key_schema = [
        {
            'AttributeName': hash_key,
            'KeyType': 'HASH',
        }
    ]
    attribute_definitions = [
        {
            'AttributeName': hash_key,
            'AttributeType': 'S',
        }
    ]

    if range_key:
        key_schema.append({'AttributeName': range_key, 'KeyType': 'RANGE'})
        attribute_definitions.append(
            {'AttributeName': range_key, 'AttributeType': 'S'})

    # Create table
    try:
        client_ddb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            # ProvisionedThroughput={
            #     'ReadCapacityUnits': 5,
            #     'WriteCapacityUnits': 5
            # },
            BillingMode='PAY_PER_REQUEST',
            OnDemandThroughput={
                'MaxReadRequestUnits': 10,
                'MaxWriteRequestUnits': 5
            }
        )

        # Wait for table creation to complete
        waiter = client_ddb.get_waiter('table_exists')
        waiter.wait(TableName=table_name, WaiterConfig={'Delay': 1})
        return table_name

    except boto3.exceptions.Boto3Error as ex:
        print(f"Error creating table: {ex}")
        return None


def load_conf_to_table(stage):
    '''Load configs from files to DDB table'''
    session = get_session()
    table_name = load_local_env_var('APP_TABLE_NAME', stage)
    conf_table = session.resource('dynamodb').Table(table_name)

    # loop for importing config files in example folder to app table
    for config_file in ['ec2_regions', 'ec2_operation', 'ec2_instance']:        
        item = load_json_file(config_file)
        try:
            conf_table.put_item(Item=item)
            print(f"- {config_file} imported.")
        except Exception as ex:
            print(f"Error importing {config_file}: {str(ex)}")            


def create_resources(stage):
    '''Create required AWS resources'''

    # Create auth_key
    create_auth_key_if_needed()

    # Create ddb tables defined in TABLES
    print("Creating Dynamodb table(s):")
    for table_config in TABLES.values():
        # Assume if it a value is recorded in .chalice config
        # file, the table already exists.
        if exist_in_config(table_config['env_var'], stage):
            print(
                f"Skipping, resource {table_config['env_var']} already exists")
            continue
        table_name = create_table(
            table_config['prefix'],
            table_config['hash_key'],
            table_config.get('range_key')
        )
        if table_name:
            print(f"- {table_name} created.")
            write_local_env_var(table_config['env_var'], table_name, stage)

    # Load example config file to database
    print("Load example configs to ddb table:")
    load_conf_to_table(stage)   


def cleanup_resources(stage):
    session = get_session()
    client_ddb = session.client('dynamodb')
    client_ssm = session.client('ssm')
    config_path = os.path.join('.chalice', 'config.json')

    with open(config_path) as f:
        config = json.load(f)
        env_vars = config['stages'].get(stage, {}).get(
            'environment_variables', {})

        for key, value in list(env_vars.items()):
            if key.endswith('_TABLE_NAME'):
                try:
                    client_ddb.delete_table(TableName=value)
                    print(f"- Table {value} deleted")
                    # remove from env variables
                    config['stages'][stage]['environment_variables'].pop(key)
                except client_ddb.exceptions.ResourceNotFoundException:
                    print(f"Table {value} not found.")
                except Exception as e:
                    print(f"Error deleting table {value}: {str(e)}")

    # write config back to file
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        f.write('\n')

    # Delete SSM parameter
    try:
        client_ssm.delete_parameter(Name=AUTH_KEY_PARAM_NAME)
        print(f"- SSM param: {AUTH_KEY_PARAM_NAME} deleted")
    except client_ssm.exceptions.ParameterNotFound:
        print(f"SSM parameter {AUTH_KEY_PARAM_NAME} not found.")
    except Exception as e:
        print(f"Error deleting SSM parameter: {str(e)}")

    print("Resources deleted.  If you haven't done so already, be "
          "sure to run 'chalice delete' to delete your Chalice application.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stage', default='dev',
                        choices=['dev', 'beta', 'prod'])
    parser.add_argument('-c', '--cleanup', action='store_true')
    # app - stores the todo items
    # users - stores the user data.
    args = parser.parse_args()

    if args.cleanup:
        cleanup_resources(args.stage)
    else:
        create_resources(args.stage)


if __name__ == '__main__':
    main()

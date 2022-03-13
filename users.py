import os
import getpass
import argparse
import hashlib
import hmac
import base64

import boto3
from boto3.dynamodb.types import Binary
from chalicelib.utils import config




def get_table_name(stage):
    '''load table name from config'''
    tableName = config.load_env_var('USERS_TABLE_NAME', stage)
    return tableName


def add_user(stage):
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    username = input('Username: ').strip()
    password = getpass.getpass('Password: ').strip()
    password_fields = _encode_password(password)
    item = {
        'username': username,
        'hash': password_fields['hash'],
        'salt': Binary(password_fields['salt']),
        'rounds': password_fields['rounds'],
        'hashed': Binary(password_fields['hashed']),
    }
    table.put_item(Item=item)


def _encode_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32)
    rounds = 100000
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                 salt, rounds)
    return {
        'hash': 'sha256',
        'salt': salt,
        'rounds': rounds,
        'hashed': hashed,
    }


def list_users(stage):
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    for item in table.scan()['Items']:
        print(item['username'])


def get_user(username, stage):
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    user_record = table.get_item(Key={'username': username}).get('Item')
    if user_record is not None:
        print(f"Entry for user: {username}")
        for key, value in user_record.items():
            if isinstance(value, Binary):
                value = base64.b64encode(value.value).decode()
            print(f"  {key:10}: {value}")


def change_passwd(stage):
    username = input('Username: ').strip()
    password = getpass.getpass('Password: ').strip()
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    item = table.get_item(Key={'username': username})['Item']
    encoded = _encode_password(password, salt=item['salt'].value)
    if hmac.compare_digest(encoded['hashed'], item['hashed'].value):
        print("Password verified.")
    else:
        print("Password verification failed.")


def test_passwd(stage):
    username = input('Username: ').strip()
    password = getpass.getpass('Password: ').strip()
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    item = table.get_item(Key={'username': username})['Item']
    encoded = _encode_password(password, salt=item['salt'].value)
    if hmac.compare_digest(encoded['hashed'], item['hashed'].value):
        print("Password verified.")
    else:
        print("Password verification failed.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--add-user', action='store_true', 
        help='add a new user')
    parser.add_argument(
        '-t', '--test-passwd', action='store_true',
        help='test the correctness of password')
    parser.add_argument(
        '-c', '--change-passwd', action='store_true',
        help='change the password')        
    parser.add_argument(
        '-l', '--list_users', action='store_true',
        help='list existed users')
    parser.add_argument(
        '-g', '--get-user',
        help='querying for user information')
    parser.add_argument('-s', '--stage', default='dev')
    
    args = parser.parse_args()
    if args.add_user:
        add_user(args.stage)
    elif args.list_users:
        list_users(args.stage)
    elif args.test_passwd:
        test_passwd(args.stage)
    elif args.change_passwd:
        change_passwd(args.stage)        
    elif args.get_user is not None:
        get_user(args.get_user, args.stage)


if __name__ == '__main__':
    main()

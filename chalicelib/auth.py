import os, base64, hashlib, hmac
import datetime
import jwt
import boto3
from uuid import uuid4
from chalice import Blueprint, UnauthorizedError

bp = Blueprint(__name__)

_USER_DB = None
_AUTH_KEY = None
_SSM_AUTH_KEY_NAME = '/ec2-quicklook/auth-key'


def get_users_db():
    global _USER_DB
    if _USER_DB is None:
        _USER_DB = boto3.resource('dynamodb').Table(
            os.environ['USERS_TABLE_NAME'])
    return _USER_DB


def get_auth_key():
    global _AUTH_KEY
    if _AUTH_KEY is None:
        base64_key = boto3.client('ssm').get_parameter(
            Name=_SSM_AUTH_KEY_NAME,
            WithDecryption=True
        )['Parameter']['Value']
        _AUTH_KEY = base64.b64decode(base64_key)
    return _AUTH_KEY


def get_jwt_token(username, password, dbrecord, secret):
    actual = hashlib.pbkdf2_hmac(
        dbrecord['hash'],
        password.encode('utf-8'),
        dbrecord['salt'].value,
        dbrecord['rounds']
    )
    expected = dbrecord['hashed'].value
    if hmac.compare_digest(actual, expected):
        now = datetime.datetime.utcnow()
        unique_id = str(uuid4())
        payload = {
            'sub': username,
            'iat': now,
            'nbf': now,
            'jti': unique_id,
            # NOTE: add 'exp' if you want tokens to expire.
        }
        return jwt.encode(payload, secret, algorithm='HS256').decode('utf-8')
    raise UnauthorizedError('Invalid password')


def decode_jwt_token(token, secret):
    return jwt.decode(token, secret, algorithms=['HS256'])

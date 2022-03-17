import os
import jinja2
import boto3
from chalice.app import Response
from chalicelib import auth, sdk, file
from . import bp, logger



_EC2_CLIENT = None

def render(templ_path, context):
    path, filename = os.path.split(templ_path)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(path or "./")).get_template(filename).render(context)


def get_ec2_client(region = 'us-east-1'):
    global _EC2_CLIENT
    if _EC2_CLIENT is None:
        _EC2_CLIENT = sdk.EC2Client(
            boto3.client('ec2', region_name=region)
        )
    return _EC2_CLIENT


def list_ec2_regions():
    aws_regions = boto3._get_default_session().get_available_regions('ec2')
    gcr_regions = boto3._get_default_session().get_available_regions('ec2', 'aws-cn')
    aws_regions.extend(gcr_regions)
    return aws_regions


@bp.route('/', methods=['GET'])
def index():
    """ec2-quicklook homepage"""
    curr_ver = 'v0.6'
    sidebar = {
        'title':bp.current_app.app_name,
        "version": curr_ver,
    }
    region_list = list_ec2_regions()

    client = get_ec2_client()
    operation_list = client.list_usage_operations()
    family_list = client.list_instance_family(
        architecture = 'arm64', 
    )
    types_list = client.get_instance_types(
        architecture = 'x86_64', 
        instance_family = 'm4'
    )
    product = {
        "title": 'demodemo',        
        "content": curr_ver,
        "create_date": ""
    }

    context = {
        'sidebar': sidebar,
        'region_list':region_list,
        'family_list':family_list,
        'types_list':types_list,
        'operation_list' : operation_list, 
        'product': product,       
    }

    html = render('chalicelib/web/template.html', context)

    return Response(
        body=html, 
        status_code=200, 
        headers={"Content-Type": "text/html"}
    )    

@bp.route("/css/{file_name}", methods=["GET"])
def get_main_css(file_name):
    """Get Web CSS Endpoint"""
    css_file = file_name+'.css'
    logger.info(f"Endpoint: Get CSS : {css_file} static file")
    try:
        content = file.get_static_file(file_name=css_file)
        return Response(
            body=content, 
            status_code=200,
            headers={"Content-Type": "text/css"},
        )
    except Exception as ex:
        return Response(
            body=f"Failed request: {css_file}. {ex}",
            status_code=404,
            headers={"Content-Type": "text/html"},
        )

@bp.route("/js/{file_name}", methods=["GET"])
def get_main_js(file_name):
    """Get Javascript Endpoint"""
    js_file = file_name+'.js'
    logger.info(f"Endpoint: Get JS : {js_file} static file")
    try:
        content = file.get_static_file(file_name=js_file)
        return Response(
            body=content, 
            status_code=200,
            headers={"Content-Type": "application/javascript; charset=utf-8"},
        )
    except Exception as ex:
        return Response(
            body=f"Failed request: {js_file}. {ex}",
            status_code=404,
            headers={"Content-Type": "text/html"},
        )

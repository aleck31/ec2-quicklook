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

@bp.route("/favicon.ico", methods=["GET"])
def get_favicon():
    """Get favicon image"""
    icon = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="96.00025019387095" height="95.9998823165437" viewBox="0 0 96.00025019387095 95.9998823165437" fill="none"><path id="分组 1" fill-rule="evenodd" style="fill:#F48D0C" transform="translate(0 0)  rotate(0 48.00012509693548 47.99994115827185)" opacity="1" d="M81.9445 81.9371C93.8445 70.0371 98.1845 53.4371 94.9745 38.1071C89.2645 38.3771 83.6445 40.6871 79.2845 45.0471L31.3145 93.0171C48.3545 99.3171 68.2545 95.6271 81.9445 81.9371Z M50.95 16.72C55.31 12.36 57.62 6.73 57.89 1.02C42.56 -2.19 25.96 2.16 14.06 14.06C0.37 27.75 -3.32 47.65 2.98 64.69L50.95 16.72Z M14.0565 81.945C17.1465 85.025 20.5465 87.605 24.1665 89.675L76.6365 37.205C81.5565 32.275 81.5565 24.295 76.6365 19.365C71.7065 14.445 63.7265 14.445 58.7965 19.365L6.32652 71.845C8.39652 75.455 10.9765 78.855 14.0565 81.945Z " /></svg>'
    return Response(
        body=icon, 
        status_code=200,
        headers={"Content-Type": "image/svg+xml"},
    )

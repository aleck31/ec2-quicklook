import os
import jinja2
import boto3
from chalice.app import Response
from chalicelib import sdk, file, config
from chalicelib.utils import build_api_endpoint
from app import logger
from . import bp

_EC2_CLIENT = None
_PRICE_CLIENT = None


def get_ec2_client(region):
    global _EC2_CLIENT
    if _EC2_CLIENT is None:
        logger.debug(f"Initializing EC2 client for region: {region}")
        _EC2_CLIENT = sdk.EC2Client(
            boto3.client('ec2', region_name=region)
        )
    return _EC2_CLIENT


def get_price_client(region = 'ap-south-1'):
    global _PRICE_CLIENT
    if _PRICE_CLIENT is None:
        logger.debug(f"Initializing pricing client for region: {region}")
        _PRICE_CLIENT = sdk.PricingClient(
            boto3.client('pricing', region_name=region)
        )
    return _PRICE_CLIENT


def render(templ_path, context):
    try:
        path, filename = os.path.split(templ_path)
        return jinja2.Environment(loader=jinja2.FileSystemLoader(path or "./")).get_template(filename).render(context)
    except Exception as ex:
        logger.error(f"Template rendering failed for {templ_path}: {str(ex)}")
        raise


def list_ec2_regions():
    try:
        # Query region list from Dynamodb table
        region_dict = config.load_config('regions')
        aws_regions = boto3._get_default_session().get_available_regions('ec2')
        gcr_regions = boto3._get_default_session().get_available_regions('ec2', 'aws-cn')
        aws_regions.extend(gcr_regions)
        region_list = [{'code':r , 'name':region_dict.get(r)} for r in aws_regions]
        return region_list
    except Exception as ex:
        logger.error(f"Failed to list EC2 regions: {str(ex)}")
        raise


@bp.route('/', methods=['GET'])
def index():
    """ec2-quicklook homepage"""
    try:
        query = bp.current_request.query_params
        #set default region: us-east-1
        region = 'us-east-1' if not query else query.get('region')
        
        region_list = list_ec2_regions()

        eclient = get_ec2_client(region)
        operation_list = eclient.list_usage_operations()
        
        #set default architecture: x86_64
        family_list = eclient.list_instance_family(
            # architecture = 'arm64', 
            architecture = 'x86_64'
        )

        pclient = get_price_client()
        voltype_list = pclient.get_attribute_values(
            service_code='AmazonEC2',
            attribute_name='volumeApiName'
        ).get('data', [])
        
        #remove sc1, st1 types that can't support system disk 
        if 'sc1' in voltype_list:
            voltype_list.remove('sc1')
        if 'st1' in voltype_list:
            voltype_list.remove('st1')

        #api docs url
        apiDocsUrl = build_api_endpoint(
            current_request=bp.current_app.current_request, 
            request_path="api/docs"
        )

        # gen blank data
        instance = {
            "productMeta": {
                "instanceFamily": "Not selected",
                "tenancy": "Shared",
                "location": region,
                "introduceUrl": "#"
            },
            "hardwareSpecs": {},
            "softwareSpecs": {},
            "productFeature": {},
            "instanceStorage": {},
            "listPrice": {
                "pricePerUnit": {
                    "currency": "USD",
                    "value": 0.00
                },
                "unit": "Hour",
                "effectiveDate": "-"
            }
        }
        volume = {
            "productMeta": {
                "volumeType": "Not selected",
                "usagetype": "-",
                "storageMedia": "-",
                "introduceUrl": "#"
            },
            "productSpecs": {},
            "listPrice": {
                "pricePerUnit": {
                    "currency": "USD",
                    "value": 0.00
                },
                "unit": "GB-Month",
                "effectiveDate": "-"
            }
        }

        # send to front-end
        context = {
            'region_list': region_list,
            'family_list': family_list,
            'voltype_list': voltype_list,
            # 'types_list':types_list,
            'operation_list': operation_list, 
            'instance': instance,
            'volume': volume,
            'apiDocsUrl': apiDocsUrl,
            'version': config.get_version('app')
        }

        return Response(
            body = render('chalicelib/webui/index.html', context),
            status_code = 200, 
            headers={"Content-Type": "text/html"}
        )
    except Exception as ex:
        logger.error(f"Homepage rendering failed: {str(ex)}")
        return Response(
            body="Internal server error",
            status_code=500,
            headers={"Content-Type": "text/html"}
        )


@bp.route('/detail', methods=['GET'])
def detail():  # Fixed duplicate function name
    """ec2 instance detail page"""
    try:
        query = bp.current_request.query_params
        #set default region: us-east-1
        region = 'us-east-1' if not query else query.get('region')
        instance_type = 'm5.xlarge' if not query else query.get('type')
        
        logger.debug(f"Processing detail page for region: {region}, instance: {instance_type}")

        #api docs url
        apiDocsUrl = build_api_endpoint(
            current_request=bp.current_app.current_request, 
            request_path="api/docs"
        )

        region_list = list_ec2_regions() 

        context = {
            'region': region,
            'region_list': region_list,
            # 'family_list' : family_list,
            'instance_type': instance_type,
            'apiDocsUrl': apiDocsUrl
        }

        return Response(
            body = render('chalicelib/webui/detail.html', context),
            status_code = 200, 
            headers={"Content-Type": "text/html"}
        )
    except Exception as ex:
        logger.error(f"Detail page rendering failed: {str(ex)}")
        return Response(
            body="Internal server error",
            status_code=500,
            headers={"Content-Type": "text/html"}
        )


@bp.route("/css/{file_name}", methods=["GET"])
def get_main_css(file_name):
    """Get Web CSS Endpoint"""
    css_file = file_name + '.css'
    try:
        content = file.get_static_file(file_name=css_file)
        return Response(
            body=content, 
            status_code=200,
            headers={"Content-Type": "text/css"},
        )
    except Exception as ex:
        logger.error(f"Failed to get CSS file {css_file}: {str(ex)}")
        return Response(
            body=f"Failed request: {css_file}. {ex}",
            status_code=404,
            headers={"Content-Type": "text/html"},
        )


@bp.route("/js/{file_name}", methods=["GET"])
def get_main_js(file_name):
    """Get Javascript Endpoint"""
    js_file = file_name + '.js'
    try:
        content = file.get_static_file(file_name=js_file)
        return Response(
            body=content, 
            status_code=200,
            headers={"Content-Type": "application/javascript; charset=utf-8"},
        )
    except Exception as ex:
        logger.error(f"Failed to get JS file {js_file}: {str(ex)}")
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

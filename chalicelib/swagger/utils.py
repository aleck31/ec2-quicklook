import boto3
import json
from typing import Dict, Any, TypedDict
from chalice import Chalice
from chalicelib.utils import build_api_endpoint, remove_base_path_slash
from .webui import docs
from app import logger


def get_swagger_ui(app: Chalice) -> str:
    """Return Swagger UI HTML page

    Args:
        app (Chalice): Pointer to main app.py

    Returns:
        str: Swagger UI HTML content

    Raises:
        Exception: If there's an error generating the Swagger UI
    """
    try:
        # Call internal API to retrieve static resource
        css_url = build_api_endpoint(
            current_request=app.current_request, 
            request_path="swagger/css"
        )
        ui_bundle_js_url = build_api_endpoint(
            current_request=app.current_request, 
            request_path="swagger/bundle"
        )    
        open_api_url = build_api_endpoint(
            current_request=app.current_request,
            request_path="api/json",
            query_params={"api_id": "", "stage": ""},
        )
        logger.debug(f"Building Swagger UI with API URL: {open_api_url}")
        logger.debug(f"swagger_ui_bundle_js url: {ui_bundle_js_url}")
        logger.debug(f"swagger_css url: {css_url}")

        html = docs.get_swagger_ui_html(
            openapi_url=open_api_url,
            title=app.app_name + " - Swagger UI",
            swagger_js_url=ui_bundle_js_url,
            swagger_css_url=css_url,
        )
        return html
    except Exception as ex:
        logger.error(f"Failed to generate Swagger UI: {str(ex)}")
        raise


def export_api_to_json(app: Chalice, exportType: str = "oas30") -> str:
    """Call AWS API Gateway Export function to generate OAS json document

    Args:
        app (Chalice): Pointer to app.py
        exportType (str, optional): ExportType (oas30 for OpenAPI 3.0,
                    swagger for Swagger/OpenAPI 2.0). Defaults to "oas30".

    Returns:
        str: Formatted JSON string containing the API specification

    Raises:
        ValueError: If required query parameters are missing
        Exception: For other API Gateway or processing errors
    """
    try:
        # Get query parameters from request with defaults
        query_params = app.current_request.query_params or {}
        api_id = query_params.get("api_id")
        api_stage = query_params.get("stage")

        if not api_id or not api_stage:
            raise ValueError("Missing required query parameters: api_id and stage")

        # send export command
        client = boto3.client("apigateway")
        export_response = client.get_export(
            restApiId=api_id,
            stageName=api_stage,
            exportType=exportType,
            parameters={"extensions": "apigateway"},
        )
        # Get streaming body from response
        streamingBody = export_response["body"]
        # Read and decode the data
        body_data = streamingBody.read()
        decoded_content = body_data.decode("utf8")
        logger.debug(decoded_content)

        # Remove basePath's slash to prevent incorrect url
        api_spec = remove_base_path_slash(json.loads(decoded_content))

        # Load the JSON to a Python list & dump it back out as formatted JSON
        result = json.dumps(api_spec, indent=4, sort_keys=False)
        return result
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise
    except Exception as ex:
        logger.error(f"Failed to export API to JSON: {str(ex)}")
        raise

from chalice.app import Response
from chalicelib.file import get_static_file
from .utils import export_api_to_json, get_swagger_ui
from app import logger
from . import bp


@bp.route("/api/docs", methods=["GET"])
def get_doc() -> Response:
    """Get Swagger UI Main Page
    
    Returns:
        Response: HTML response containing the Swagger UI page with Content-Type text/html
    """
    logger.debug("Generating Swagger UI page")
    html = get_swagger_ui(bp.current_app)
    return Response(
        body=html, 
        status_code=200,
        headers={"Content-Type": "text/html"},
    )


@bp.route("/api/json", methods=["GET"])
def get_api_jsonb() -> Response:
    """Get OpenAPI specification in JSON format
    
    Returns:
        Response: JSON response containing the OpenAPI specification
    """
    logger.debug("Exporting API to JSON")
    return export_api_to_json(bp.current_app)


@bp.route("/swagger/css", methods=["GET"])
def get_swagger_css() -> Response:
    """Get Swagger UI CSS Endpoint
    
    Returns:
        Response: CSS response from static folder with Content-Type text/css,
                 or 404 error response if file not found
    """
    css_file = "swagger-ui.css"
    try:
        content = get_static_file(file_name=css_file)
        return Response(
            body=content, 
            status_code=200,
            headers={"Content-Type": "text/css"},
        )
    except Exception as ex:
        logger.error(f"Failed to get Swagger CSS file: {str(ex)}")
        return Response(
            body=f"Failed request: {css_file}. {ex}",
            status_code=404,
            headers={"Content-Type": "text/html"}
        )


@bp.route("/swagger/bundle", methods=["GET"])
def get_swagger_ui_bundle() -> Response:
    """Get Swagger UI Bundle JS Endpoint
    
    Returns:
        Response: JavaScript bundle from static folder with Content-Type application/javascript,
                 or 404 error response if file not found
    """
    ui_js_file = "swagger-ui-bundle.js"
    try:
        content = get_static_file(file_name=ui_js_file)
        return Response(
            body=content,
            status_code=200,
            headers={"Content-Type": "application/javascript; charset=utf-8"},
        )
    except Exception as ex:
        logger.error(f"Failed to get Swagger UI bundle: {str(ex)}")
        return Response(
            body=f"{ui_js_file} not found. {ex}", 
            status_code=404,
            headers={"Content-Type": "text/html"},
        )

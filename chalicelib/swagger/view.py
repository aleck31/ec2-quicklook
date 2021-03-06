from chalice.app import Response
from chalicelib.file import get_static_file
from .utils import export_api_to_json, get_swagger_ui
from . import bp, logger


@bp.route("/api/docs", methods=["GET"])
def get_doc():
    """Get Swagger UI Main Page

    Returns:
        str: text/html for Swagger UI page
    """
    html = get_swagger_ui(bp.current_app)
    return Response(
        body=html, 
        status_code=200,
        headers={"Content-Type": "text/html"},
    )


@bp.route("/api/json", methods=["GET"])
def get_api_jsonb():
    return export_api_to_json(bp.current_app)


@bp.route("/swagger/css", methods=["GET"])
def get_swagger_css():
    """Get Swagger UI CSS Endpoint

    Returns:
        str: CSS Content from Static folder
    """
    css_file = "swagger-ui.css"
    logger.info(f"Endpoint: Get CSS : {css_file} static file")
    try:
        content = get_static_file(file_name=css_file)
        return Response(
            body=content, 
            status_code=200,
            headers={"Content-Type": "text/css"},
        )
    except Exception as ex:
        return Response(
            body=f"Failed request: {css_file}. {ex}",
            status_code=404,
            headers={"Content-Type": "text/html"}
        )


@bp.route("/swagger/bundle", methods=["GET"])
def get_swagger_ui_bundle():
    """Get Swagger UI Bundle JS Endpoint

    Returns:
        str: Return JavaScript for Swagger UI from static folder
    """
    ui_js_file = "swagger-ui-bundle.js"
    logger.info(f"Endpoint: Get JS : {ui_js_file} static file")
    try:
        content = get_static_file(file_name=ui_js_file)
        return Response(
            body=content,
            status_code=200,
            headers={"Content-Type": "application/javascript; charset=utf-8"},
        )
    except Exception as ex:
        return Response(
            body=f"{ui_js_file} not found. {ex}", 
            status_code=404,
            headers={"Content-Type": "text/html"},
        )


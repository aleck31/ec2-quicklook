from chalice import Blueprint

# Create blueprint instance
bp = Blueprint(__name__)

# Import views after bp is defined to avoid circular imports
__import__('chalicelib.product.view')

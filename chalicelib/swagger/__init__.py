import logging
from chalice import Blueprint


bp = Blueprint(__name__)

# Get logger
logger = logging.getLogger()

from . import view

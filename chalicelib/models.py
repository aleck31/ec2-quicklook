from typing import Dict, Any, Optional

# Exception Classes
class AWSServiceError(Exception):
    """Base exception for AWS service-related errors"""
    def __init__(self, message: str, service: str, error_code: str = None):
        self.service = service
        self.error_code = error_code
        super().__init__(f"{service} error: {message}")

class EC2ServiceError(AWSServiceError):
    """Specific exception for EC2 service errors"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, "EC2", error_code)

class PricingServiceError(AWSServiceError):
    """Specific exception for Pricing service errors"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, "Pricing", error_code)

# Simple type aliases for request parameters
InstanceProductParams = Dict[str, str]
VolumeProductParams = Dict[str, str]

# Type hints for responses
ProductResponse = Dict[str, Any]

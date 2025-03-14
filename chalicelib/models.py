from typing import Dict, Any, Optional, TypedDict, NotRequired, Literal

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

# Type definitions for request parameters
class InstanceProductParams(TypedDict):
    """Parameters for EC2 instance product queries"""
    region: str  # AWS region code
    typesize: str   # Instance type with size (e.g., 't3.micro')
    op: str     # Operation type
    option: NotRequired[Literal['OnDemand']]  # Market option, defaults to 'OnDemand'
    tenancy: NotRequired[Literal['Shared', 'Dedicated', 'Host']]  # Instance tenancy, defaults to 'Shared'

class VolumeProductParams(TypedDict):
    """Parameters for EBS volume product queries"""
    region: str  # AWS region code
    type: str   # Volume type (e.g., 'gp3')
    size: str   # Volume size in GB
    option: NotRequired[Literal['OnDemand']]  # Market option, defaults to 'OnDemand'

# Type hints for responses
ProductResponse = Dict[str, Any]

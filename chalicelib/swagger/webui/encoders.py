from enum import Enum
from pathlib import PurePath
from types import GeneratorType
from typing import Any, Callable, Dict, Optional, Set, Union
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


SetIntStr = Set[Union[int, str]]
DictIntStrAny = Dict[Union[int, str], Any]

class JsonSerializable:
    """Base class for JSON serializable objects"""
    def to_dict(self) -> dict:
        return vars(self)

# Converting Python Objects to JSON-Compatible Formats
def jsonable_encoder(
    obj: Any,
    include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: Dict[Any, Callable[[Any], Any]] = {},
    sqlalchemy_safe: bool = True,
) -> Any:
    if include is not None and not isinstance(include, set):
        include = set(include)
    if exclude is not None and not isinstance(exclude, set):
        exclude = set(exclude)

    def encode_object(obj: Any) -> Any:
        if isinstance(obj, JsonSerializable):
            return encode_object(obj.to_dict())
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, PurePath):
            return str(obj)
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {
                encode_object(key): encode_object(value)
                for key, value in obj.items()
                if (not sqlalchemy_safe or not isinstance(key, str) or not key.startswith("_sa"))
                and (value is not None or not exclude_none)
                and ((not include) or key in include)
                and ((not exclude) or key not in exclude)
            }
        elif isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
            return [encode_object(item) for item in obj]
        
        if custom_encoder:
            if type(obj) in custom_encoder:
                return custom_encoder[type(obj)](obj)
            for encoder_type, encoder in custom_encoder.items():
                if isinstance(obj, encoder_type):
                    return encoder(obj)
        
        # Fallback for objects
        try:
            return encode_object(dict(obj))
        except:
            try:
                return encode_object(vars(obj))
            except:
                return str(obj)

    return encode_object(obj)

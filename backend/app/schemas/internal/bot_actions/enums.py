from enum import Enum


class ActionVariableType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    OBJECT = "object"
    ARRAY = "array"


class ActionAuthType(str, Enum):
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    CUSTOM = "custom"


class ApiKeyLocation(str, Enum):
    HEADER = "header"
    QUERY = "query"


class ActionResponseType(str, Enum):
    JSON = "json"
    TEXT = "text"


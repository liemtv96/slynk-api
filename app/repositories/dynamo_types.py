from decimal import Decimal


def to_dynamo_value(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [to_dynamo_value(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dynamo_value(item) for key, item in value.items()}
    return value

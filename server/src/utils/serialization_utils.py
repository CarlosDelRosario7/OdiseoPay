from datetime import date, datetime
from decimal import Decimal


def serialize_model(instance, hidden=()):
    result = {}
    for column in instance.__table__.columns:
        if column.name in hidden or column.key in hidden:
            continue
        value = getattr(instance, column.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = str(value)
        result[column.name] = value
    return result

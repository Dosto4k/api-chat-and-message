from rest_framework import status
from rest_framework.serializers import ValidationError


def validate_limit_query_param(limit: str) -> int:
    try:
        int_limit: int = int(limit)
    except (ValueError, TypeError) as err:
        raise ValidationError(
            detail={
                "invalid query parameter": (
                    "Query-параметр 'limit' должен быть типом 'int'."
                ),
            },
            code=status.HTTP_400_BAD_REQUEST,
        ) from err
    if not 1 <= int_limit <= 100:
        raise ValidationError(
            detail={
                "invalid query parameter": (
                    "Query-параметр 'limit' должен быть в диапазоне 1 <= limit <= 100."
                ),
            },
            code=status.HTTP_400_BAD_REQUEST,
        )
    return int_limit

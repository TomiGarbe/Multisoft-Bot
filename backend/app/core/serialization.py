from __future__ import annotations

from datetime import datetime

from fastapi.encoders import ENCODERS_BY_TYPE

from app.core.datetime_utils import encode_datetime_for_response


def configure_datetime_encoder() -> None:
    ENCODERS_BY_TYPE[datetime] = encode_datetime_for_response

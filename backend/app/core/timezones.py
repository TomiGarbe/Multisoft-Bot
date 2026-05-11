from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TENANT_TIMEZONE = "UTC"


@dataclass(frozen=True)
class TimezoneOption:
    value: str
    label: str


LATAM_TIMEZONE_OPTIONS: tuple[TimezoneOption, ...] = (
    TimezoneOption(value="America/Argentina/Cordoba", label="Argentina - Cordoba"),
    TimezoneOption(value="America/Argentina/Buenos_Aires", label="Argentina - Buenos Aires"),
    TimezoneOption(value="America/Santiago", label="Chile - Santiago"),
    TimezoneOption(value="America/Montevideo", label="Uruguay - Montevideo"),
    TimezoneOption(value="America/Sao_Paulo", label="Brasil - Sao Paulo"),
    TimezoneOption(value="America/Asuncion", label="Paraguay - Asuncion"),
    TimezoneOption(value="America/Lima", label="Peru - Lima"),
    TimezoneOption(value="America/Bogota", label="Colombia - Bogota"),
    TimezoneOption(value="America/Mexico_City", label="Mexico - Ciudad de Mexico"),
    TimezoneOption(value="America/La_Paz", label="Bolivia - La Paz"),
)

SUPPORTED_TENANT_TIMEZONES: frozenset[str] = frozenset(option.value for option in LATAM_TIMEZONE_OPTIONS)


def is_valid_iana_timezone(value: str) -> bool:
    try:
        ZoneInfo(value)
        return True
    except ZoneInfoNotFoundError:
        return False


def is_supported_tenant_timezone(value: str) -> bool:
    return value in SUPPORTED_TENANT_TIMEZONES and is_valid_iana_timezone(value)

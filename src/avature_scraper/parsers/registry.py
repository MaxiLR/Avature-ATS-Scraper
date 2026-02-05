from urllib.parse import urlparse

from .base import BaseJobParser
from .baufest import BaufestParser
from .gps import GPSHospitalityParser
from .nva import NVAParser
from .standard import StandardAvatureParser

DOMAIN_PARSERS: dict[str, type[BaseJobParser]] = {
    "baufest.avature.net": BaufestParser,
    "gpshospitality.avature.net": GPSHospitalityParser,
    "nva.avature.net": NVAParser,
}

_parser_cache: dict[str, BaseJobParser] = {}


class ParserRegistry:
    """Registry for domain-specific parsers."""

    @staticmethod
    def get_parser(domain: str) -> BaseJobParser:
        if domain in _parser_cache:
            return _parser_cache[domain]

        parser_class = DOMAIN_PARSERS.get(domain, StandardAvatureParser)
        parser = parser_class()
        _parser_cache[domain] = parser
        return parser

    @staticmethod
    def register(domain: str, parser_class: type[BaseJobParser]):
        DOMAIN_PARSERS[domain] = parser_class
        if domain in _parser_cache:
            del _parser_cache[domain]


def get_parser(url_or_domain: str) -> BaseJobParser:
    if url_or_domain.startswith("http"):
        domain = urlparse(url_or_domain).netloc
    else:
        domain = url_or_domain
    return ParserRegistry.get_parser(domain)

"""phone-harvest: Extract phone numbers from text, files, and web pages."""

__version__ = "0.1.0"

from phone_extractor.extractor import PhoneExtractor
from phone_extractor.utils import PhoneResult

__all__ = ["PhoneExtractor", "PhoneResult", "__version__"]

"""email-harvest: Extract email addresses from text, files, and web pages."""

__version__ = "0.1.0"

from email_extractor.extractor import EmailExtractor
from email_extractor.utils import EmailResult

__all__ = ["EmailExtractor", "EmailResult", "__version__"]

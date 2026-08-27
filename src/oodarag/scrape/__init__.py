"""Web scraping: robots-aware fetching, HTML-to-text extraction, crawling."""

from oodarag.scrape.html import ExtractedPage, extract
from oodarag.scrape.robots import RobotsPolicy

__all__ = ["ExtractedPage", "extract", "RobotsPolicy"]

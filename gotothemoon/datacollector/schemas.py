"""
Defines the data structures (schemas) for the data collected by the system.

Using dataclasses to ensure a consistent structure for the JSON output.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class BaseSchema:
    """
    A base class for all schemas. Contains fields that are common and always
    required (non-default).
    """
    id: str
    source: str
    country: str
    published_at: str

@dataclass
class NewsSchema(BaseSchema):
    """Schema for news articles."""
    # Non-default fields specific to News
    headline: str
    url: str
    content: str

    # Fields with default values
    category: str = "news"
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    company_symbol: Optional[str] = None
    duplicate_count: int = 1

@dataclass
class DisclosureSchema(BaseSchema):
    """Schema for company disclosures from DART/EDGAR."""
    # Non-default fields specific to Disclosures
    report_title: str
    company_name: str
    company_symbol: str
    url_to_document: str
    filing_type: str

    # Fields with default values
    category: str = "disclosure"
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    summary: Optional[str] = None

@dataclass
class ResearchSchema(BaseSchema):
    """Schema for brokerage research reports."""
    # Non-default fields specific to Research
    report_title: str
    firm_name: str
    company_symbol: str

    # Fields with default values
    category: str = "research"
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    analyst_name: Optional[str] = None
    rating: Optional[str] = None
    target_price: Optional[float] = None
    summary: Optional[str] = None
    url_to_report: Optional[str] = None

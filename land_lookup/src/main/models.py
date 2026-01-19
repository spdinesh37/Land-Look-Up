# requirements.txt
# fastapi==0.104.1
# uvicorn==0.24.0
# httpx==0.25.0
# pydantic==2.5.0
# python-dotenv==1.0.0

# ============================================
# models.py - DTOs
# ============================================
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class PropertySearchRequest(BaseModel):
    """
    Search fields matching WCAD preliminary search:
    - Zip Code
    - Total Acres
    - Deed Date
    - Seller
    - Buyer
    - Sale Date
    """
    zip_code: Optional[str] = None
    total_acres: Optional[float] = None  # Exact acres
    min_acres: Optional[float] = None  # Or range
    max_acres: Optional[float] = None
    deed_date: Optional[date] = None  # Exact date
    deed_date_from: Optional[date] = None  # Or range
    deed_date_to: Optional[date] = None
    sale_date: Optional[date] = None  # Exact date
    sale_date_from: Optional[date] = None  # Or range
    sale_date_to: Optional[date] = None
    seller: Optional[str] = None
    buyer: Optional[str] = None


class PropertyResponse(BaseModel):
    """Property result matching WCAD detail page"""
    property_id: str
    quick_ref_id: Optional[str] = None

    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None

    # Property details
    total_acres: Optional[float] = None
    legal_description: Optional[str] = None

    # Sale information
    sale_date: Optional[str] = None
    sale_price: Optional[float] = None
    deed_date: Optional[str] = None

    # Parties
    seller: Optional[str] = None
    buyer: Optional[str] = None

    # Link to detail page
    detail_url: Optional[str] = None

    # Source dataset
    source: str = "PropertyDataExport"  # or "Preliminary" or "RecentSales"


class SearchResponse(BaseModel):
    """Paginated response"""
    results: List[PropertyResponse]
    total_count: int
    page: int
    page_size: int
    sources_searched: List[str]  # Which datasets were queried


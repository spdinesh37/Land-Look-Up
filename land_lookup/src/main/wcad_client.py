# ============================================
# wcad_client.py - API Client for all 3 datasets
# ============================================
import httpx
from typing import Dict, List, Any, Optional
from config import settings


class WCADApiClient:
    """
    Client for all 3 WCAD datasets:
    1. Sale-PropertyDataExport (pvyy-mm8r) - Main sales data
    2. Sale-Preliminary (8p3y-6p23) - Preliminary sales
    3. Recent-Sales-Preliminary (wdp6-f3zg) - Recent preliminary
    """

    def __init__(self):
        self.base_url = settings.WCAD_BASE_URL
        self.headers = {
            "X-App-Token": settings.WCAD_APP_TOKEN,
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=settings.API_TIMEOUT)

    async def close(self):
        await self.client.aclose()

    def _build_where_clause(self, filters: Dict[str, Any]) -> Optional[str]:
        """
        Build SoQL WHERE clause from search fields

        NOTE: PropertyDataExport dataset doesn't always have 'saledate' field
        Most records only have 'deeddate' field
        Available fields: propertyid, deeddate, prevownername (seller)
        """
        conditions = []

        # Property ID - if provided
        if filters.get('property_id'):
            conditions.append(f"propertyid='{filters['property_id']}'")

        # Deed Date - exact or range (this is the reliable date field)
        if filters.get('deed_date'):
            conditions.append(f"deeddate='{filters['deed_date']}T00:00:00.000'")
        else:
            if filters.get('deed_date_from'):
                conditions.append(f"deeddate>='{filters['deed_date_from']}T00:00:00.000'")
            if filters.get('deed_date_to'):
                conditions.append(f"deeddate<='{filters['deed_date_to']}T00:00:00.000'")

        # Sale Date - use deed date as fallback since saledate field often missing
        # If user provides sale_date filters, apply them to deeddate instead
        if not filters.get('deed_date') and not filters.get('deed_date_from') and not filters.get('deed_date_to'):
            if filters.get('sale_date'):
                conditions.append(f"deeddate='{filters['sale_date']}T00:00:00.000'")
            else:
                if filters.get('sale_date_from'):
                    conditions.append(f"deeddate>='{filters['sale_date_from']}T00:00:00.000'")
                if filters.get('sale_date_to'):
                    conditions.append(f"deeddate<='{filters['sale_date_to']}T00:00:00.000'")

        # Seller - partial match (prevownername field in PropertyDataExport)
        if filters.get('seller'):
            conditions.append(f"upper(prevownername) LIKE upper('%{filters['seller']}%')")

        return " AND ".join(conditions) if conditions else None

    async def search_sale_property_export(self, filters: Dict[str, Any],
                                          limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Search Sale-PropertyDataExport (pvyy-mm8r)
        This is the main sales dataset
        """
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "deeddate DESC"
        }

        where_clause = self._build_where_clause(filters)
        if where_clause:
            params["$where"] = where_clause

        url = f"{self.base_url}{settings.SALE_PROPERTY_EXPORT}"

        print(f"[PropertyDataExport] Query: {url}")
        print(f"[PropertyDataExport] WHERE: {where_clause}")

        response = await self.client.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def search_sale_preliminary(self, filters: Dict[str, Any],
                                      limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Search Sale-Preliminary (8p3y-6p23)
        Preliminary/pending sales
        """
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "deeddate DESC"
        }

        where_clause = self._build_where_clause(filters)
        if where_clause:
            params["$where"] = where_clause

        url = f"{self.base_url}{settings.SALE_PRELIMINARY}"

        print(f"[SalePreliminary] Query: {url}")
        print(f"[SalePreliminary] WHERE: {where_clause}")

        response = await self.client.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def search_recent_sales_preliminary(self, filters: Dict[str, Any],
                                              limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Search Recent-Sales-Preliminary (wdp6-f3zg)
        Most recent preliminary sales
        """
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "deeddate DESC"
        }

        where_clause = self._build_where_clause(filters)
        if where_clause:
            params["$where"] = where_clause

        url = f"{self.base_url}{settings.RECENT_SALES_PRELIMINARY}"

        print(f"[RecentSalesPreliminary] Query: {url}")
        print(f"[RecentSalesPreliminary] WHERE: {where_clause}")

        response = await self.client.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _build_property_where_clause(self, filters: Dict[str, Any]) -> Optional[str]:
        """
        Build WHERE clause for property dataset (an3x-cnmw)
        This dataset has: pstlzip5, assessedacres, siteaddress, propertyid
        """
        conditions = []

        # Zip code - uses pstlzip5 field
        if filters.get('zip_code'):
            conditions.append(f"pstlzip5='{filters['zip_code']}'")

        # Acres - uses assessedacres field
        if filters.get('total_acres'):
            conditions.append(f"assessedacres={filters['total_acres']}")
        else:
            if filters.get('min_acres'):
                conditions.append(f"assessedacres>={filters['min_acres']}")
            if filters.get('max_acres'):
                conditions.append(f"assessedacres<={filters['max_acres']}")

        return " AND ".join(conditions) if conditions else None

    async def search_property_parcels(self, filters: Dict[str, Any],
                                      limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Search Property Parcels dataset (an3x-cnmw)
        This has zip_code (pstlzip5) and acres (assessedacres)
        """
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "propertyid"
        }

        where_clause = self._build_property_where_clause(filters)
        if where_clause:
            params["$where"] = where_clause

        url = f"{self.base_url}{settings.PROPERTY_PARCELS}"

        print(f"[PropertyParcels] Query: {url}")
        print(f"[PropertyParcels] WHERE: {where_clause}")

        response = await self.client.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
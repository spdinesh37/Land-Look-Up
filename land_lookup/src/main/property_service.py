# ============================================
# property_service.py - Business Logic
# ============================================
from typing import Dict, List, Any

from models import PropertySearchRequest, PropertyResponse, SearchResponse
from wcad_client import WCADApiClient
from config import settings


class PropertyService:
    """
    Service to search across all 3 datasets and combine results
    """

    def __init__(self):
        self.wcad_client = WCADApiClient()

    async def search_properties(self, request: PropertySearchRequest,
                                page: int = 1, page_size: int = 20,
                                search_all_datasets: bool = True) -> SearchResponse:
        """
        Search properties across one or all datasets
        """

        # Build filters from request
        filters = self._build_filters(request)
        offset = (page - 1) * page_size

        print(f"[PropertyService] Starting search with filters: {filters}")

        all_results = []
        sources_searched = []

        # 1. Always search main Sale-PropertyDataExport dataset
        try:
            print(f"[PropertyService] Searching PropertyDataExport...")
            main_data = await self.wcad_client.search_sale_property_export(
                filters, limit=page_size, offset=offset
            )
            mapped_results = self._map_to_response(main_data, "PropertyDataExport")
            all_results.extend(mapped_results)
            sources_searched.append("Sale-PropertyDataExport")
            print(f"[PropertyService] ✓ Found {len(main_data)} in PropertyDataExport, mapped to {len(mapped_results)} results")
        except Exception as e:
            print(f"[PropertyService] ✗ Error in PropertyDataExport: {e}")

        # 2. Optionally search Sale-Preliminary
        if search_all_datasets:
            try:
                print(f"[PropertyService] Searching Preliminary...")
                prelim_data = await self.wcad_client.search_sale_preliminary(
                    filters, limit=page_size, offset=offset
                )
                mapped_prelim = self._map_to_response(prelim_data, "Preliminary")
                all_results.extend(mapped_prelim)
                sources_searched.append("Sale-Preliminary")
                print(f"[PropertyService] ✓ Found {len(prelim_data)} in Preliminary")
            except Exception as e:
                print(f"[PropertyService] ✗ Error in Preliminary: {e}")

        # 3. Optionally search Recent-Sales-Preliminary
        if search_all_datasets:
            try:
                print(f"[PropertyService] Searching RecentSales...")
                recent_data = await self.wcad_client.search_recent_sales_preliminary(
                    filters, limit=page_size, offset=offset
                )
                mapped_recent = self._map_to_response(recent_data, "RecentSales")
                all_results.extend(mapped_recent)
                sources_searched.append("Recent-Sales-Preliminary")
                print(f"[PropertyService] ✓ Found {len(recent_data)} in RecentSales")
            except Exception as e:
                print(f"[PropertyService] ✗ Error in RecentSales: {e}")

        # Remove duplicates and limit to page_size
        unique_results = self._deduplicate(all_results)[:page_size]

        print(f"[PropertyService] Total results after dedup: {len(unique_results)}")

        return SearchResponse(
            results=unique_results,
            total_count=len(unique_results),
            page=page,
            page_size=page_size,
            sources_searched=sources_searched
        )

    def _build_filters(self, request: PropertySearchRequest) -> Dict[str, Any]:
        """Convert request to filter dict"""
        filters = {}

        if request.zip_code:
            filters['zip_code'] = request.zip_code

        if request.total_acres:
            filters['total_acres'] = request.total_acres
        elif request.min_acres or request.max_acres:
            if request.min_acres:
                filters['min_acres'] = request.min_acres
            if request.max_acres:
                filters['max_acres'] = request.max_acres

        if request.deed_date:
            filters['deed_date'] = request.deed_date
        elif request.deed_date_from or request.deed_date_to:
            if request.deed_date_from:
                filters['deed_date_from'] = request.deed_date_from
            if request.deed_date_to:
                filters['deed_date_to'] = request.deed_date_to

        if request.sale_date:
            filters['sale_date'] = request.sale_date
        elif request.sale_date_from or request.sale_date_to:
            if request.sale_date_from:
                filters['sale_date_from'] = request.sale_date_from
            if request.sale_date_to:
                filters['sale_date_to'] = request.sale_date_to

        if request.seller:
            filters['seller'] = request.seller
        if request.buyer:
            filters['buyer'] = request.buyer

        return filters

    def _map_to_response(self, data: List[Dict], source: str) -> List[PropertyResponse]:
        """Map API data to PropertyResponse using actual field names"""
        results = []
        for item in data:
            # Build detail URL if we have the quickrefid
            detail_url = None
            quick_ref = item.get('quickrefid')
            if quick_ref:
                detail_url = f"{settings.WCAD_SEARCH_URL}/Property-Detail/PropertyQuickRefID/{quick_ref}"

            results.append(PropertyResponse(
                property_id=item.get('propertyid', 'N/A'),
                quick_ref_id=quick_ref,
                address=item.get('propertynumber'),  # This is property number, not street address
                city=None,  # Not available in these datasets
                zip_code=None,  # Not available in these datasets
                total_acres=None,  # Not available in these datasets
                legal_description=None,  # Not available in these datasets
                sale_date=item.get('saledate', '').split('T')[0] if item.get('saledate') else None,
                sale_price=None,  # Not available in these datasets
                deed_date=item.get('deeddate', '').split('T')[0] if item.get('deeddate') else None,
                seller=item.get('prevownername'),  # Previous owner is seller
                buyer=None,  # Not directly available
                detail_url=detail_url,
                source=source
            ))
        return results

    def _deduplicate(self, results: List[PropertyResponse]) -> List[PropertyResponse]:
        """Remove duplicates based on property_id"""
        seen = set()
        unique = []
        for result in results:
            if result.property_id not in seen:
                seen.add(result.property_id)
                unique.append(result)
        return unique

    async def close(self):
        await self.wcad_client.close()
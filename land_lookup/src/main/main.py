# ============================================
# main.py - FastAPI Application - COMPLETE VERSION
# ============================================
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from models import PropertySearchRequest, PropertyResponse, SearchResponse
from property_service import PropertyService
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.property_service = PropertyService()
    yield
    await app.state.property_service.close()


app = FastAPI(
    title="Williamson County Property Search API",
    description="Search across Sale-PropertyDataExport, Sale-Preliminary, and Recent-Sales-Preliminary",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "WCAD Property Search API",
        "endpoints": {
            "debug": "/api/debug/sample-data",
            "test": "/api/test/recent-sales",
            "search_dates": "/api/properties/by-dates",
            "search_location": "/api/properties/by-location",
            "docs": "/docs"
        }
    }


@app.get("/api/test/recent-sales")
async def test_recent_sales(limit: int = Query(10, le=50)):
    """
    TEST ENDPOINT: Get the most recent sales (no filters)
    This helps verify the API is working

    Example: /api/test/recent-sales?limit=10
    """
    service: PropertyService = app.state.property_service
    client = service.wcad_client

    try:
        # Get recent sales without any filters
        url = f"{client.base_url}{settings.SALE_PROPERTY_EXPORT}"
        response = await client.client.get(
            url,
            params={"$limit": limit, "$order": "saledate DESC"},
            headers=client.headers
        )
        data = response.json()

        return {
            "message": "Most recent sales (no filters)",
            "count": len(data),
            "sales": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/sample-data")
async def get_sample_data():
    """
    DEBUG ENDPOINT: Get sample data from each dataset to discover actual field names
    Visit: http://localhost:8000/api/debug/sample-data
    """
    service: PropertyService = app.state.property_service
    client = service.wcad_client

    results = {}

    # Dataset 1: Sale-PropertyDataExport
    try:
        url = f"{client.base_url}{settings.SALE_PROPERTY_EXPORT}"
        response = await client.client.get(url, params={"$limit": 1}, headers=client.headers)
        data = response.json()
        results["PropertyDataExport"] = {
            "url": url,
            "status": response.status_code,
            "sample_record": data[0] if data else None,
            "available_fields": list(data[0].keys()) if data else []
        }
    except Exception as e:
        results["PropertyDataExport"] = {"error": str(e)}

    # Dataset 2: Sale-Preliminary
    try:
        url = f"{client.base_url}{settings.SALE_PRELIMINARY}"
        response = await client.client.get(url, params={"$limit": 1}, headers=client.headers)
        data = response.json()
        results["SalePreliminary"] = {
            "url": url,
            "status": response.status_code,
            "sample_record": data[0] if data else None,
            "available_fields": list(data[0].keys()) if data else []
        }
    except Exception as e:
        results["SalePreliminary"] = {"error": str(e)}

    # Dataset 3: Recent-Sales-Preliminary
    try:
        url = f"{client.base_url}{settings.RECENT_SALES_PRELIMINARY}"
        response = await client.client.get(url, params={"$limit": 1}, headers=client.headers)
        data = response.json()
        results["RecentSalesPreliminary"] = {
            "url": url,
            "status": response.status_code,
            "sample_record": data[0] if data else None,
            "available_fields": list(data[0].keys()) if data else []
        }
    except Exception as e:
        results["RecentSalesPreliminary"] = {"error": str(e)}

    # Dataset 4: Property Parcels
    try:
        url = f"{client.base_url}{settings.PROPERTY_PARCELS}"
        response = await client.client.get(url, params={"$limit": 1}, headers=client.headers)
        data = response.json()
        results["PropertyParcels"] = {
            "url": url,
            "status": response.status_code,
            "sample_record": data[0] if data else None,
            "available_fields": list(data[0].keys()) if data else []
        }
    except Exception as e:
        results["PropertyParcels"] = {"error": str(e)}

    return results


@app.get("/api/properties/by-dates")
async def search_by_dates(
        sale_date_from: Optional[str] = None,
        sale_date_to: Optional[str] = None,
        deed_date_from: Optional[str] = None,
        deed_date_to: Optional[str] = None,
        seller: Optional[str] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
):
    """
    Search by dates and seller name

    Example: /api/properties/by-dates?sale_date_from=2021-01-01&sale_date_to=2021-12-31&seller=KNOWLES
    """
    request = PropertySearchRequest(
        sale_date_from=sale_date_from,
        sale_date_to=sale_date_to,
        deed_date_from=deed_date_from,
        deed_date_to=deed_date_to,
        seller=seller
    )

    try:
        service: PropertyService = app.state.property_service
        return await service.search_properties(request, page, page_size, True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/by-location")
async def search_by_location(
        zip_code: Optional[str] = None,
        min_acres: Optional[float] = None,
        max_acres: Optional[float] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100)
):
    """
    Search by ZIP CODE and ACRES

    Example: /api/properties/by-location?zip_code=78641&min_acres=10&max_acres=50
    """
    service: PropertyService = app.state.property_service
    client = service.wcad_client

    try:
        filters = {}
        if zip_code:
            filters['zip_code'] = zip_code
        if min_acres:
            filters['min_acres'] = min_acres
        if max_acres:
            filters['max_acres'] = max_acres

        offset = (page - 1) * page_size
        data = await client.search_property_parcels(filters, limit=page_size, offset=offset)

        # Map property parcel data to response
        results = []
        for item in data:
            results.append(PropertyResponse(
                property_id=item.get('propertyid', 'N/A'),
                quick_ref_id=None,
                address=item.get('siteaddress'),
                city=item.get('pstlcity'),
                zip_code=item.get('pstlzip5'),
                total_acres=float(item.get('assessedacres', 0)) if item.get('assessedacres') else None,
                legal_description=None,
                sale_date=None,
                sale_price=None,
                deed_date=None,
                seller=None,
                buyer=item.get('ownernme1'),  # Current owner
                detail_url=None,
                source="PropertyParcels"
            ))

        return SearchResponse(
            results=results,
            total_count=len(results),
            page=page,
            page_size=page_size,
            sources_searched=["PropertyParcels"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/properties/search", response_model=SearchResponse)
async def search_properties_post(
        request: PropertySearchRequest,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        all_datasets: bool = Query(True, description="Search all 3 datasets or just main one")
):
    """
    POST search with JSON body
    """
    try:
        service: PropertyService = app.state.property_service
        return await service.search_properties(request, page, page_size, all_datasets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/search", response_model=SearchResponse)
async def search_properties_get(
        zip_code: Optional[str] = None,
        total_acres: Optional[float] = None,
        min_acres: Optional[float] = None,
        max_acres: Optional[float] = None,
        deed_date: Optional[str] = None,
        deed_date_from: Optional[str] = None,
        deed_date_to: Optional[str] = None,
        sale_date: Optional[str] = None,
        sale_date_from: Optional[str] = None,
        sale_date_to: Optional[str] = None,
        seller: Optional[str] = None,
        buyer: Optional[str] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        all_datasets: bool = Query(True)
):
    """
    GET search with query parameters
    """
    request = PropertySearchRequest(
        zip_code=zip_code,
        total_acres=total_acres,
        min_acres=min_acres,
        max_acres=max_acres,
        deed_date=deed_date,
        deed_date_from=deed_date_from,
        deed_date_to=deed_date_to,
        sale_date=sale_date,
        sale_date_from=sale_date_from,
        sale_date_to=sale_date_to,
        seller=seller,
        buyer=buyer
    )

    try:
        service: PropertyService = app.state.property_service
        return await service.search_properties(request, page, page_size, all_datasets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
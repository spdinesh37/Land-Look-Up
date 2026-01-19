# ============================================
# config.py
# ============================================
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WCAD_BASE_URL: str = "https://data.wcad.org"
    WCAD_SEARCH_URL: str = "https://search.wcad.org"
    WCAD_APP_TOKEN: str = "o9NY7r7FdFUFpFQQC9vAgy7Jx"
    API_TIMEOUT: int = 30

    # Dataset endpoints
    SALE_PROPERTY_EXPORT: str = "/resource/pvyy-mm8r.json"
    SALE_PRELIMINARY: str = "/resource/8p3y-6p23.json"
    RECENT_SALES_PRELIMINARY: str = "/resource/wdp6-f3zg.json"
    PROPERTY_PARCELS: str = "/resource/an3x-cnmw.json"  # Add this line

    class Config:
        env_file = ".env"

settings = Settings()

'''
Now **make sure you've updated these 3 files:**

1. ✅ `config.py` - Added PROPERTY_PARCELS
2. ⚠️ `wcad_client.py` - Replace with the version I gave you above
3. ⚠️ `property_service.py` - Replace with the version I gave you above  
4. ✅ `main.py` - Should already be updated

After updating all files, **restart the server** and try:
'''
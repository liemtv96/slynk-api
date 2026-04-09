import os

from mangum import Mangum

from main import app

handler = Mangum(app, api_gateway_base_path=os.getenv("SLYNK_API_GATEWAY_BASE_PATH", "/"))

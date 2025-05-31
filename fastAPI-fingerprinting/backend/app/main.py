from dotenv import load_dotenv
from app.database import engine, Base  
load_dotenv(".env")     # đọc biến trước khi bất kỳ module nào lấy os.getenv
from fastapi import FastAPI, Request, Response
from app.routes.auth_routes import auth_router
from app.routes.order_routes import order_router
from app.routes.verify import verify_router
from fastapi_jwt_auth import AuthJWT
from app.schemas import Settings
import inspect, re
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.openapi.utils import get_openapi
import json
import time
from app.middleware.middleware_request import LogRequestMiddleware
from hashlib import sha256
from app.middleware.fingerprintHTTP_create import fingerprint_middleware
from app.middleware.fingerprintHTTP_create import generate_fingerprint
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.models import delete_expired_tokens
from contextlib import asynccontextmanager
from app.middleware.request_logger import RequestLoggerMiddleware


#scheduler = BackgroundScheduler()
scheduler = AsyncIOScheduler()



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Đợi Postgres sẵn (thử 10 lần, mỗi 2 giây)
    from sqlalchemy.exc import OperationalError
    for _ in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except OperationalError:
            import asyncio, time
            print(" Waiting for Postgres…")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Postgres not ready!")

    scheduler.add_job(delete_expired_tokens, "interval", minutes=1)
    scheduler.start()
    print("Scheduler started ")
    yield
    scheduler.shutdown()
    print("Scheduler stopped ")

app=FastAPI(lifespan=lifespan)


app.add_middleware(RequestLoggerMiddleware)   
app.middleware("http")(fingerprint_middleware)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title = "testing API - checking fingerprint",
        version = "1.0",
        description = "an API for checking function of fingerprint",
        routes = app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter: **'Bearer &lt;JWT&gt;'**, where JWT is the access token"
        }
    }

    # Get all routes where jwt_optional() or jwt_required
    api_router = [route for route in app.routes if isinstance(route, APIRoute)]

    for route in api_router:
        path = getattr(route, "path")
        endpoint = getattr(route,"endpoint")
        methods = [method.lower() for method in getattr(route, "methods")]

        for method in methods:
            # access_token
            if (
                re.search("jwt_required", inspect.getsource(endpoint)) or
                re.search("fresh_jwt_required", inspect.getsource(endpoint)) or
                re.search("jwt_optional", inspect.getsource(endpoint))
            ):
                openapi_schema["paths"][path][method]["security"] = [
                    {
                        "Bearer Auth": []
                    }
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi



@AuthJWT.load_config
def get_config():
    return Settings()

app.include_router(auth_router)
app.include_router(order_router)

@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)
async def proxy_pass_through(full_path: str, request: Request):
    """
    catch 302 OK after checking in middleware.
    
    """
    return Response(status_code=302)
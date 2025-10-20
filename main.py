from dotenv import load_dotenv
load_dotenv()

import os, re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.responses import JSONResponse

from app.api import router

app = FastAPI()

ALLOWED_ORIGINS = [
    # Local dev
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:4201",
    "http://127.0.0.1:4201",
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # Vercel PROD (dominio estable para entregar)
    "https://2024-plaza-final-front.vercel.app",
]

ALLOWED_ORIGIN_REGEX = r"^https://2024-plaza-final-front(?:-[a-z0-9-]+)?-cplaza-finals-projects\.vercel\.app$"

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Requested-With",
    "Accept",
    "Origin",
]
EXPOSE_HEADERS = ["Authorization"]
ALLOW_CREDENTIALS = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    expose_headers=EXPOSE_HEADERS,
)

DEV_DEBUG = os.getenv("DEV_DEBUG", "true").lower() in ("1", "true", "yes")
_origin_regex = re.compile(ALLOWED_ORIGIN_REGEX)

@app.middleware("http")
async def ensure_cors_on_errors(request, call_next):
    origin = request.headers.get("origin", "")
    try:
        response = await call_next(request)
    except HTTPException as http_exc:
        response = JSONResponse({"detail": http_exc.detail}, status_code=http_exc.status_code)
    except Exception as exc:
        if DEV_DEBUG:
            import traceback
            traceback.print_exc()
            response = JSONResponse({"detail": f"{type(exc).__name__}: {str(exc)}"}, status_code=500)
        else:
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)

    origin_allowed = origin in ALLOWED_ORIGINS or bool(_origin_regex.match(origin))
    if origin_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        if ALLOW_CREDENTIALS:
            response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
# ==========================================================================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="C&V BAR API",
        version="1.0.0",
        description="Doc interactiva con JWT Firebase 🔐",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {"type": "http", "scheme": "bearer"}
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"HTTPBearer": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(router)

# main.py
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi import HTTPException
from starlette.responses import JSONResponse

from app.api import router

app = FastAPI()

ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:4201",
    "http://127.0.0.1:4201",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Requested-With",
    "Accept",
    "Origin",
]
EXPOSE_HEADERS = ["Authorization"]

# CORS estándar
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    expose_headers=EXPOSE_HEADERS,
)

# ===== DEBUG MIDDLEWARE: mostrar el error real en respuestas 500 =====
# Úsalo en desarrollo para ver el "detail" exacto del crash.
DEV_DEBUG = os.getenv("DEV_DEBUG", "true").lower() in ("1", "true", "yes")

@app.middleware("http")
async def ensure_cors_on_errors(request, call_next):
    origin = request.headers.get("origin")
    try:
        response = await call_next(request)
    except HTTPException as http_exc:
        # Preservar mensajes de HTTPException
        response = JSONResponse({"detail": http_exc.detail}, status_code=http_exc.status_code)
    except Exception as exc:
        # Mostrar detalle real SOLO en dev
        if DEV_DEBUG:
            import traceback
            traceback.print_exc()
            response = JSONResponse({"detail": f"{type(exc).__name__}: {str(exc)}"}, status_code=500)
        else:
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)

    # Inyectar CORS si el origen es permitido
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
# =====================================================================

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

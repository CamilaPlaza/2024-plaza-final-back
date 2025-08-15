from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer

from app.db.firebase import db

from app.api import router

app = FastAPI()

origins = [
    "http://localhost:4201", 
    "https://two024-ranchoaparte-back.onrender.com",
    "http://localhost:3000",
    "https://2024-messidepaul-front.vercel.app", 
    "https://2024-ranchoaparte-front-ivory.vercel.app",
    "http://2024-huidobro-front.vercel.app",
    "https://2024-huidobro-front-ey08brtzo-josehuidobro1s-projects.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
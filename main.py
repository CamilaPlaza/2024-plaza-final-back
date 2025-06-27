from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
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
    allow_headers=["*"],
)

# ✅ Swagger: Auth global con bearer token
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Tu API Rancho Aparte",
        version="1.0.0",
        description="Documentación interactiva con autenticación JWT Firebase 🔐",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"HTTPBearer": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Rutas
app.include_router(router)

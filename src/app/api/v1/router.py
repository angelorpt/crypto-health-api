"""Agregador de rotas da versão v1 (`/api/v1`)."""

from fastapi import APIRouter

from app.api.v1 import auth, demo, health, medical_records, users

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(demo.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(medical_records.router)

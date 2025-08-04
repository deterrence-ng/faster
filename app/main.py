#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2024-10-16 19:44:54
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.access_control import router as access_control_router
from app.user import router as users_router
from app.utils.image_qr import configure_storage_cors

app = FastAPI()

admin_routes = APIRouter(prefix="/admin")
users_routes = APIRouter(prefix="/users")
public_routes = APIRouter(prefix="/public")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configure_storage_cors()

# Access Control
app.include_router(access_control_router.perms_router)
app.include_router(access_control_router.roles_router)
app.include_router(access_control_router.groups_router)

# Users
app.include_router(users_router.users_router)
app.include_router(users_router.public_users_router)

# Auth
app.include_router(users_router.auth_router)
admin_routes.include_router(users_router.admin_auth_router)
users_routes.include_router(users_router.users_auth_router)


app.include_router(admin_routes)
app.include_router(users_routes)
app.include_router(public_routes)

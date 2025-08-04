#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-06 20:59:07
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


from typing import Any, Generator
import jwt
from fastapi import (
    Depends,
    HTTPException,
    WebSocket,
    WebSocketException,
    status,
    Query,
)
from fastapi.security import OAuth2PasswordBearer

from app.config import database as db
from app.config.config import settings
from app.user import cruds as users_cruds, schemas as users_schema
from app.utils.crud_util import CrudUtil


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.token_url)


def get_db() -> Generator[Any, Any, Any]:
    dbase = db.SessionLocal()
    try:
        yield dbase
    finally:
        dbase.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme), cu: CrudUtil = Depends(CrudUtil)
) -> users_schema.UserSchema:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token {e}")

    user: users_schema.UserSchema = users_schema.UserSchema.model_validate(
        await users_cruds.get_user_by_email(cu, payload["data"]["email"])
    )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


def get_current_ws_user(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    cu: CrudUtil = Depends(CrudUtil),
) -> users_schema.UserSchema:

    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing token"
        )

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except Exception:
        print("failed to decode token")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token"
        )

    user: users_schema.UserSchema = users_schema.UserSchema.model_validate(
        users_cruds.get_user_by_email(cu, payload["data"]["email"])
    )

    if not user.is_active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user"
        )

    return user


def get_super_user(
    cu: CrudUtil = Depends(CrudUtil),
) -> users_schema.UserSchema:
    # get the first user in the system
    user: users_schema.UserSchema = users_schema.UserSchema.model_validate(
        users_cruds.get_super_admin(cu)
    )

    return user


def get_auth_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


class HasPermission:
    def __init__(self, perms: list[str]):
        self.perms = perms

    def __call__(
        self, user: users_schema.UserSchema = Depends(get_current_user)
    ) -> None:
        for perm in self.perms:
            if perm not in user.permissions:
                raise HTTPException(status_code=403, detail="Permission denied")

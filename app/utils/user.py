#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-07 12:38:04
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
import jwt

import bcrypt

from app.config.config import settings
from app.mixins.commons import Token


def verify_password(plain_password: str, hashed_password: str) -> bool:
    verified: bool = bcrypt.checkpw(
        password=plain_password.encode("utf-8"),
        hashed_password=hashed_password.encode("utf-8"),
    )
    return verified


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hash: str = bcrypt.hashpw(password=password.encode("utf-8"), salt=salt).decode()
    return hash


# valid for 100 years
def machine_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone(timedelta(hours=1))) + timedelta(
        days=365 * 100  # 100 years validity
    )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_mobile_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone(timedelta(hours=1))) + timedelta(
        days=settings.token_mobile_life_span
    )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone(timedelta(hours=1))) + timedelta(
        hours=settings.token_life_span
    )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        decoded: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token {e}")

    return decoded


def get_access_token(data: dict[str, Any], is_mobile: bool = False) -> Token:
    if is_mobile:
        token = create_mobile_access_token(data)

        return Token(
            access_token=token,
            token_type="bearer",
            permissions=[],
        )

    token = create_access_token(data)
    return Token(
        access_token=token,
        token_type="bearer",
        permissions=[],
    )

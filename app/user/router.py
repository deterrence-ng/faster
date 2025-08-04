#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-09-19 22:37:46
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


from datetime import datetime
from typing import Any
from fastapi.param_functions import Path
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends

from app.access_control.cruds import get_group_by_name
from app.dependencies import dependencies as deps
from app.user import cruds, schemas
from app.utils.crud_util import CrudUtil
from app.utils.user import (
    create_access_token,
    create_mobile_access_token,
    machine_access_token,
)


users_router = APIRouter(
    prefix="/users",
    tags=["User"],
    dependencies=[
        Depends(deps.get_current_user),
    ],
)

public_users_router = APIRouter(
    prefix="/users",
    tags=["User"],
)

users_auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

admin_auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/docs-token",
    include_in_schema=False,
)
async def docs_authentication(
    cu: CrudUtil = Depends(CrudUtil),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    user = await cruds.authenticate_docs_user(
        cu=cu, email_or_phone=str(form_data.username), password=form_data.password
    )

    token_data_to_encode = {
        "data": {
            "uuid": user.uuid,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "permissions": user.permissions,
        }
    }
    access_token = create_access_token(token_data_to_encode)
    return schemas.Token(access_token=access_token, token_type="bearer")


@users_auth_router.post(
    "/token",
    response_model=schemas.Token,
)
async def users_login(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    user_data: schemas.Login,
) -> schemas.Token:
    user: schemas.UserSchema = await cruds.authenticate_user(
        cu,
        str(user_data.email_or_phone),
        user_data.password,
    )

    validation_key: str = await cruds.get_user_validation_key(cu, user.uuid)

    token_data_to_encode = {
        "data": {
            "uuid": user.uuid,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "user_group": user.groups[0].name if user.groups else None,
            "validation_key": validation_key,
        }
    }

    access_token = create_access_token(token_data_to_encode)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_group=user.groups[0].name if user.groups else None,
        permissions=user.permissions,
    )


@admin_auth_router.post(
    "/token",
    response_model=schemas.Token,
)
async def admin_login(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    user_data: schemas.Login,
) -> schemas.Token:
    user: schemas.UserSchema = await cruds.authenticate_admin_user(
        cu,
        str(user_data.email_or_phone),
        user_data.password,
    )

    validation_key: str = await cruds.get_user_validation_key(cu, user.uuid)

    token_data_to_encode = {
        "data": {
            "uuid": user.uuid,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "user_group": user.groups[0].name if user.groups else None,
            "validation_key": validation_key,
        }
    }

    access_token = create_access_token(token_data_to_encode)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_group=user.groups[0].name if user.groups else None,
        permissions=user.permissions,
    )


@users_auth_router.post(
    "/mobile/token",
    response_model=schemas.Token,
)
async def users_mobile_login(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    user_data: schemas.Login,
) -> schemas.Token:
    user: schemas.UserSchema = await cruds.authenticate_user(
        cu,
        str(user_data.email_or_phone),
        user_data.password,
    )

    validation_key: str = await cruds.get_user_validation_key(cu, user.uuid)

    token_data_to_encode = {
        "data": {
            "uuid": user.uuid,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "user_group": user.groups[0].name if user.groups else None,
            "validation_key": validation_key,
        }
    }

    access_token = create_mobile_access_token(token_data_to_encode)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_group=user.groups[0].name if user.groups else None,
        permissions=user.permissions,
    )


@auth_router.post(
    "/reset-password/request-otp",
)
async def request_password_reset_otp(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    password_reset: schemas.PasswordResetRequest,
) -> dict[str, Any]:
    return await cruds.request_password_reset_otp(cu, password_reset)


@auth_router.post(
    "/reset-password/verify-otp",
)
async def verify_password_reset_otp(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    verify_otp: schemas.PasswordResetVerifyOTP,
) -> dict[str, Any]:
    return await cruds.verify_password_reset_otp(cu, verify_otp)


@auth_router.post(
    "/reset-password/set-password",
)
async def reset_password(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    password_reset: schemas.PasswordReset,
    user: schemas.UserSchema = Depends(deps.get_current_user),
) -> dict[str, Any]:
    return await cruds.reset_password(cu, password_reset, user)


@auth_router.put(
    "/change-password/own",
)
async def change_own_password(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    password_change: schemas.PasswordChangeRequest,
    user: schemas.UserSchema = Depends(deps.get_current_user),
) -> dict[str, str]:
    return await cruds.change_own_password(cu, password_change, user)


@auth_router.post(
    "/machine-token",
    response_model=schemas.Token,
    dependencies=[Depends(deps.HasPermission(["auth:generate_machine_token"]))],
    description="Generate a long-lived machine token for system integrations. Admin use only.",
)
async def generate_machine_token(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    user: schemas.UserSchema = Depends(deps.get_super_user),
) -> schemas.Token:
    """
    Generate a machine token for API integrations.
    This token has a very long expiry (100 years) and should be used
    only for secure system-to-system integrations.
    """
    validation_key: str = await cruds.get_user_validation_key(cu, user.uuid)

    token_data_to_encode = {
        "data": {
            "uuid": user.uuid,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "user_group": user.groups[0].name if user.groups else None,
            "is_machine": True,
            "created_at": datetime.now().isoformat(),
            "validation_key": validation_key,
        }
    }

    access_token = machine_access_token(token_data_to_encode)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user_group=user.groups[0].name if user.groups else None,
        permissions=user.permissions,
    )


@auth_router.get(
    "/me",
    response_model=schemas.UserSchema,
    description="Get the profile of the currently logged in user",
)
async def get_own_profile(
    *,
    user: schemas.UserSchema = Depends(deps.get_current_user),
) -> schemas.UserSchema:
    """
    Retrieve the profile of the currently authenticated user.
    This endpoint returns the complete profile of the user making the request.
    """
    return await cruds.get_own_user_profile(user)


@users_router.post(
    "", status_code=201, dependencies=[Depends(deps.HasPermission(["admin:create"]))]
)
async def create_admin_user(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    user_data: schemas.UserIn,
) -> schemas.UserSchema:
    user = await cruds.create_user(cu, user_data, is_admin=True)
    return schemas.UserSchema.model_validate(user)


@users_router.get(
    "",
    response_model=schemas.UserList,
    dependencies=[Depends(deps.HasPermission(["admin:list"]))],
)
async def list_admin_users(
    cu: CrudUtil = Depends(CrudUtil),
    filter: schemas.AdminUserFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
) -> schemas.UserList:
    return await cruds.list_admin_users(cu, filter, skip=skip, limit=limit)


@users_router.get("/{uuid}", dependencies=[Depends(deps.HasPermission(["admin:read"]))])
async def get_admin_detail(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
) -> schemas.UserSchema:
    user = await cruds.get_user_by_uuid(cu, uuid)
    return schemas.UserSchema.model_validate(user)


@users_router.put(
    "/{uuid}", dependencies=[Depends(deps.HasPermission(["admin:update"]))]
)
async def update_admin(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
    user_data: schemas.UserUpdate,
) -> schemas.UserSchema:
    user = await cruds.update_user(cu, uuid, user_data)
    return schemas.UserSchema.model_validate(user)


@users_router.put(
    "/change_password/{user_uuid}",
    dependencies=[Depends(deps.HasPermission(["admin:update"]))],
)
async def change_admin_password(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    user_uuid: str = Path(...),
) -> schemas.PasswordChangeOut:
    return await cruds.change_admin_password(cu, user_uuid)


@users_router.delete(
    "/{uuid}", dependencies=[Depends(deps.HasPermission(["admin:delete"]))]
)
async def delete_admin(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
) -> dict[str, Any]:
    return await cruds.delete_user(cu, uuid)


@users_router.post(
    "/{uuid}/groups", dependencies=[Depends(deps.HasPermission(["admin:update"]))]
)
async def add_group_to_user(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
    groups: schemas.UserGroup,
) -> schemas.UserSchema:
    user = await cruds.get_user_by_uuid(cu, uuid)
    group_list = groups.model_dump().pop("groups")

    for group_name in group_list:
        group = await get_group_by_name(cu, name=group_name)
        user.groups.append(group)

    await cu.db.commit()
    await cu.db.refresh(user)
    return schemas.UserSchema.model_validate(user)


@users_router.delete(
    "/{uuid}/groups/{group_name}",
    dependencies=[Depends(deps.HasPermission(["admin:update"]))],
)
async def remove_group_from_user(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
    group_name: str,
) -> schemas.UserSchema:
    user = await cruds.get_user_by_uuid(cu, uuid=uuid)

    group = await get_group_by_name(cu, group_name)
    user.groups.remove(group)

    await cu.db.commit()
    await cu.db.refresh(user)
    return schemas.UserSchema.model_validate(user)

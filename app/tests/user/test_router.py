#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2023-01-30 07:10:12
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from pathlib import Path
from fastapi.testclient import TestClient
from app.tests.utils.utils import gen_user, gen_uuid
from app.user import models, schemas, cruds
from app.utils.crud_util import CrudUtil
from app.utils.misc import gen_email, gen_random_password


def test_login(
    client: TestClient,
    admin_user: models.User,
    create_account_mailbox: Path,
) -> None:
    password = create_account_mailbox.read_text().strip()

    response = client.post(
        "/auth/token",
        json=schemas.Login(
            email_or_phone=str(admin_user.email),
            password=password,
        ).model_dump(),
    )
    res_payload = response.json()

    assert response.status_code == 200
    assert "access_token" in res_payload
    assert "permissions" in res_payload


def test_login_with_phone(
    client: TestClient,
    admin_user: models.User,
    create_account_mailbox: Path,
) -> None:
    password = create_account_mailbox.read_text().strip()

    response = client.post(
        "/auth/token",
        json=schemas.Login(
            email_or_phone=str(admin_user.phone),
            password=password,
        ).model_dump(),
    )
    res_payload = response.json()

    assert response.status_code == 200
    assert "access_token" in res_payload
    assert "permissions" in res_payload


def test_login_mobile(
    client: TestClient,
    admin_user: models.User,
    create_account_mailbox: Path,
) -> None:
    password = create_account_mailbox.read_text().strip()

    response = client.post(
        "/auth/mobile/token",
        json=schemas.Login(
            email_or_phone=str(admin_user.email),
            password=password,
        ).model_dump(),
    )
    res_payload = response.json()

    assert response.status_code == 200
    assert "access_token" in res_payload
    assert "permissions" in res_payload


def test_login_with_wrong_password(
    client: TestClient,
    admin_user: models.User,
) -> None:
    response = client.post(
        "/auth/token",
        json=schemas.Login(
            email_or_phone=str(admin_user.email),
            password=gen_random_password(),
        ).model_dump(),
    )
    res_payload = response.json()

    assert response.status_code == 400
    assert "detail" in res_payload
    assert res_payload["detail"] == "Email and password do not match"


def test_login_with_wrong_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/token",
        json=schemas.Login(
            email_or_phone=gen_email(),
            password=gen_random_password(),
        ).model_dump(),
    )

    res_payload = response.json()

    assert response.status_code == 400
    assert "detail" in res_payload
    assert res_payload["detail"] == "Email and password do not match"


def test_login_with_inactive_user(
    client: TestClient,
    inactive_admin_user: models.User,
    create_account_mailbox: Path,
) -> None:
    password = create_account_mailbox.read_text().strip()
    response = client.post(
        "/auth/token",
        json=schemas.Login(
            email_or_phone=str(inactive_admin_user.email),
            password=password,
        ).model_dump(),
    )

    res_payload = response.json()

    assert response.status_code == 400
    assert "detail" in res_payload
    assert res_payload["detail"] == "Email and password do not match"


def test_request_password_reset(
    client: TestClient,
    admin_user: models.User,
    password_reset_mailbox: Path,
) -> None:
    response = client.post(
        "/auth/forgot-password",
        params={"email": str(admin_user.email)},
    )

    res_payload = response.json()

    token = password_reset_mailbox.read_text().strip()

    assert "reset-password" in token
    assert response.status_code == 200
    assert "detail" in res_payload
    assert res_payload["detail"] == "We've sent a password reset link to your mail"


def test_request_password_reset_wrong_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/forgot-password",
        params={"email": gen_email()},
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "detail" in res_payload
    assert res_payload["detail"] == "We've sent a password reset link to your mail"


def test_reset_password(
    client: TestClient,
    crud_util: CrudUtil,
    admin_user: models.User,
    password_reset_mailbox: Path,
) -> None:
    cruds.reset_password(
        crud_util,
        str(admin_user.email),
    )

    token = password_reset_mailbox.read_text().strip().split("/")[-1]

    response = client.post(f"/auth/reset-password/{token}")

    res_payload = response.json()
    print(token)
    assert response.status_code == 200
    assert "detail" in res_payload
    assert "Password reset successful" in res_payload["detail"]


def test_reset_password_wrong_token(
    client: TestClient,
) -> None:
    response = client.post(f"/auth/reset-password/{gen_random_password()}")

    res_payload = response.json()

    assert response.status_code == 400
    assert "detail" in res_payload
    assert "Invalid token" in res_payload["detail"]


def test_create_admin_user(
    client: TestClient,
    su_token_headers: dict[str, str],
    crud_util: CrudUtil,
) -> None:
    user_data = gen_user().model_dump()

    response = client.post(
        "/users",
        json=user_data,
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 201
    assert "id" in res_payload
    assert res_payload["email"] == user_data["email"]
    assert res_payload["is_active"] is True


def test_create_admin_user_with_existing_email(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    user_data = gen_user().model_dump()

    user_data["email"] = admin_user.email

    response = client.post(
        "/users",
        json=user_data,
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 409
    assert "detail" in res_payload
    assert res_payload["detail"] == "User already exists"


def test_create_admin_user_no_login(
    client: TestClient,
) -> None:
    user_data = gen_user().model_dump()

    response = client.post(
        "/users",
        json=user_data,
    )

    res_payload = response.json()

    assert response.status_code == 401

    assert res_payload["detail"] == "Not authenticated"


def test_list_admin_users(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.get(
        "/users",
        headers=su_token_headers,
        params={"skip": 1, "limit": 2},
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "items" in res_payload
    assert len(res_payload["items"]) == 2


def test_list_admin_users_no_login(
    client: TestClient,
) -> None:
    response = client.get(
        "/users",
    )

    res_payload = response.json()

    assert response.status_code == 401
    assert res_payload["detail"] == "Not authenticated"


def test_list_admin_users_not_found(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.get(
        "/users", headers=su_token_headers, params={"email": gen_email()}
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "items" in res_payload
    assert len(res_payload["items"]) == 0


def test_get_admin_detail(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    response = client.get(
        f"/users/{admin_user.uuid}",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "uuid" in res_payload
    assert res_payload["uuid"] == admin_user.uuid


def test_get_admin_detail_no_login(
    client: TestClient,
    admin_user: models.User,
) -> None:
    response = client.get(
        f"/users/{admin_user.uuid}",
    )

    res_payload = response.json()

    assert response.status_code == 401
    assert res_payload["detail"] == "Not authenticated"


def test_get_admin_detail_not_found(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"/users/{gen_uuid()}",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 404
    assert "detail" in res_payload
    assert res_payload["detail"] == "User not found"


def test_update_admin_user(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    user_data = gen_user().model_dump()
    assert user_data["email"] != admin_user.email

    response = client.put(
        f"/users/{admin_user.uuid}",
        json=user_data,
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "uuid" in res_payload
    assert res_payload["uuid"] == admin_user.uuid
    assert res_payload["email"] == user_data["email"]


def test_update_admin_user_no_login(
    client: TestClient,
    admin_user: models.User,
) -> None:
    response = client.put(
        f"/users/{admin_user.uuid}",
        json=gen_user().model_dump(),
    )

    res_payload = response.json()

    assert response.status_code == 401
    assert res_payload["detail"] == "Not authenticated"


def test_update_admin_user_not_found(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.put(
        f"/users/{gen_uuid()}",
        json=gen_user().model_dump(),
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 404
    assert "detail" in res_payload
    assert res_payload["detail"] == "User not found"


def test_change_admin_password(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    response = client.put(
        f"/users/change_password/{admin_user.uuid}",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "password" in res_payload


def test_change_admin_password_no_login(
    client: TestClient,
    admin_user: models.User,
) -> None:
    response = client.put(
        f"/users/change_password/{admin_user.uuid}",
    )

    res_payload = response.json()

    assert response.status_code == 401
    assert res_payload["detail"] == "Not authenticated"


def test_change_admin_password_not_found(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.put(
        f"/users/change_password/{gen_uuid()}",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 404
    assert "detail" in res_payload
    assert res_payload["detail"] == "User not found"


def test_delete_admin_user(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    response = client.delete(
        f"/users/{admin_user.uuid}",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert "status" in res_payload
    assert "success" in res_payload["status"]


def test_delete_admin_user_no_login(
    client: TestClient,
    admin_user: models.User,
) -> None:
    response = client.delete(
        f"/users/{admin_user.uuid}",
    )

    res_payload = response.json()

    assert response.status_code == 401
    assert res_payload["detail"] == "Not authenticated"


def test_delete_admin_user_not_found(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.delete(
        f"/users/{gen_uuid()}",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 404
    assert "detail" in res_payload
    assert res_payload["detail"] == "User not found"


def test_add_group_to_user(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    response = client.post(
        f"/users/{admin_user.uuid}/groups",
        json={"groups": ["super_user_group"]},
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert res_payload["uuid"] == admin_user.uuid


def test_add_group_to_user_no_login(
    client: TestClient,
    admin_user: models.User,
) -> None:
    response = client.post(
        f"/users/{admin_user.uuid}/groups",
        json={"groups": ["super_user_group"]},
    )

    res_payload = response.json()

    assert response.status_code == 401
    assert res_payload["detail"] == "Not authenticated"


def test_add_group_to_user_not_found(
    client: TestClient,
    su_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"/users/{gen_uuid()}/groups",
        json={"groups": ["super_user_group"]},
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 404
    assert "detail" in res_payload
    assert res_payload["detail"] == "User not found"


def test_add_group_to_user_invalid(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    response = client.post(
        f"/users/{admin_user.uuid}/groups",
        json={"groups": ["non_super_user_group"]},
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 404
    assert "detail" in res_payload
    assert res_payload["detail"] == "Group not found"


def test_remove_group_from_user(
    client: TestClient,
    su_token_headers: dict[str, str],
    admin_user: models.User,
) -> None:
    client.post(
        f"/users/{admin_user.uuid}/groups",
        json={"groups": ["super_user_group"]},
        headers=su_token_headers,
    )

    response = client.delete(
        f"/users/{admin_user.uuid}/groups/super_user_group",
        headers=su_token_headers,
    )

    res_payload = response.json()

    assert response.status_code == 200
    assert res_payload["uuid"] == admin_user.uuid

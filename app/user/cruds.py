from typing import Any
from fastapi import HTTPException
from sqlalchemy import Result, Select, select

from app.config.config import settings
from app.user import schemas, models
from app.utils.crud_util import CrudUtil
from app.utils.mail import (
    send_account_create_mail,
)
from app.utils.misc import (
    async_send_otp_to_email,
    async_send_otp_to_phone,
    async_verify_email_otp,
    async_verify_phone_otp,
    gen_random_password,
)
from app.utils.sms import send_account_creation_sms
from app.utils.user import get_access_token, get_password_hash, verify_password


async def create_user(
    cu: CrudUtil,
    user_data: schemas.UserIn,
    autocommit: bool = True,
    is_admin: bool = False,
    can_login: bool = True,
) -> models.User:
    # password and hash generated
    # in class using validators
    user_to_create = schemas.UserCreate(
        **user_data.model_dump(),
        password_hash="",
        is_admin=is_admin,
        can_login=can_login,
    )

    await cu.ensure_unique(
        model_to_check=models.User, unique_condition={"email": user_data.email}
    )

    user: models.User = await cu.create_model(
        model_to_create=models.User, create=user_to_create, autocommit=autocommit
    )

    if is_admin or can_login:
        # todo: update this we use OTP
        send_account_create_mail(
            str(user.email), user_to_create.password, str(user.firstname)
        )

    return user


async def create_machine_user(
    cu: CrudUtil,
) -> models.User:
    # generate the machine user
    to_create = schemas.UserIn(
        email="machine@diacyber.com",
        firstname="MACHINE",
        lastname="USER",
        middlename="SYSTEM",
        phone="04041344134",
        password=gen_random_password(),
    )

    # create the user
    return await create_user(
        cu,
        user_data=to_create,
        autocommit=True,
        is_admin=True,
        can_login=True,
    )


async def generate_machine_user_keys(
    cu: CrudUtil,
):
    pass


async def activate_user(
    cu: CrudUtil,
    uuid: str,
    autocommit: bool = True,
    send_mail: bool = False,
    send_sms: bool = False,
) -> models.User:
    db_user: models.User = await get_user_by_uuid(cu, uuid)
    user_active = schemas.UserActivate(password="", password_hash="")

    db_user.can_login = user_active.can_login  # type: ignore
    db_user.temp_password_hash = user_active.password_hash  # type: ignore
    if send_mail:
        send_account_create_mail(
            str(db_user.email), user_active.password, str(db_user.firstname)
        )

    if send_sms:
        send_account_creation_sms(
            str(db_user.phone),
            str(db_user.phone),
            user_active.password,
            str(db_user.firstname),
        )

    if autocommit:
        await cu.db.commit()
        await cu.db.refresh(db_user)

    return db_user


async def get_user_by_email(cu: CrudUtil, email: str) -> models.User:
    user: models.User = await cu.get_model_or_404(
        model_to_get=models.User, model_conditions={"email": email}
    )

    return user


async def get_user_validation_key(cu: CrudUtil, uuid: str) -> str:
    user: models.User = await get_user_by_uuid(cu, uuid)

    if not user.validation_key:
        raise HTTPException(status_code=404, detail="User validation key not found")

    return user.validation_key


async def get_user_by_phone(cu: CrudUtil, phone: str) -> models.User:
    user: models.User = await cu.get_model_or_404(
        model_to_get=models.User, model_conditions={"phone": phone}
    )

    return user


async def get_super_admin(cu: CrudUtil) -> models.User:
    super_user_id = settings.super_user_id
    # order by id
    query: Select = (
        select(models.User)
        .filter(models.User.uuid == super_user_id)
        .order_by(models.User.id.asc())
    )

    result: Result[Any] = await cu.db.execute(query)
    user: models.User | None = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Super admin not found")

    return user


async def get_user_by_uuid(
    cu: CrudUtil,
    uuid: str,
) -> models.User:
    user: models.User = await cu.get_model_or_404(
        model_to_get=models.User, model_conditions={"uuid": uuid}
    )
    return user


async def get_own_user_profile(
    user: schemas.UserSchema,
) -> schemas.UserSchema:
    return user


async def update_user(
    cu: CrudUtil,
    uuid: str,
    user_data: schemas.UserUpdate | schemas.UserUpdateSelf,
    autocommit: bool = True,
) -> models.User:
    user: models.User = await cu.update_model(
        model_to_update=models.User,
        update=user_data,
        update_conditions={"uuid": uuid},
        autocommit=autocommit,
    )

    return user


async def delete_user(
    cu: CrudUtil, uuid: str, autocommit: bool = True
) -> dict[str, Any]:
    return await cu.delete_model(
        model_to_delete=models.User,
        delete_conditions={"uuid": uuid},
        autocommit=autocommit,
    )


async def authenticate_user(
    cu: CrudUtil,
    email_or_phone: str,
    password: str,
) -> schemas.UserSchema:
    try:
        user: models.User = await get_user_by_email(cu, email_or_phone)
    except HTTPException as e:
        if e.status_code == 404:
            try:
                user = await get_user_by_phone(cu, email_or_phone)
            except HTTPException:
                raise HTTPException(
                    status_code=400, detail="Login Credentials do not match"
                )
        else:
            raise HTTPException(
                status_code=400, detail="Login Credentials do not match"
            )

    # check the user is admin and disallow them
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    if not user.is_active or not user.can_login:
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    if not verify_password(password, str(user.password_hash)):
        # check whether it's a temp password
        temp_password = str(user.temp_password_hash)
        if temp_password == "None":
            raise HTTPException(
                status_code=400, detail="Login Credentials do not match"
            )

        if temp_password and verify_password(password, temp_password):
            user.password_hash = temp_password
            user.temp_password_hash = ""
            await cu.db.commit()
            return schemas.UserSchema.model_validate(user)
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    return schemas.UserSchema.model_validate(user)


async def authenticate_admin_user(
    cu: CrudUtil,
    email_or_phone: str,
    password: str,
) -> schemas.UserSchema:
    try:
        user: models.User = await get_user_by_email(cu, email_or_phone)
        print(user.email)
    except HTTPException as e:
        if e.status_code == 404:
            try:
                user = await get_user_by_phone(cu, email_or_phone)
            except HTTPException:
                raise HTTPException(
                    status_code=400, detail="Login Credentials do not match"
                )
        else:
            raise HTTPException(
                status_code=400, detail="Login Credentials do not match"
            )

    # check the user is admin and disallow them
    if not user.is_admin:
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    if not user.is_active or not user.can_login:  # type: ignore
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    if not verify_password(password, str(user.password_hash)):
        # check whether it's a temp password
        temp_password = str(user.temp_password_hash)
        if temp_password == "None":
            raise HTTPException(
                status_code=400, detail="Login Credentials do not match"
            )

        if temp_password and verify_password(password, temp_password):
            user.password_hash = temp_password  # type: ignore
            user.temp_password_hash = ""  # type: ignore
            await cu.db.commit()
            return schemas.UserSchema.model_validate(user)
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    return schemas.UserSchema.model_validate(user)


async def authenticate_docs_user(
    cu: CrudUtil,
    email_or_phone: str,
    password: str,
) -> schemas.UserSchema:
    try:
        user: models.User = await get_user_by_email(cu, email_or_phone)
    except HTTPException as e:
        if e.status_code == 404:
            try:
                user = await get_user_by_phone(cu, email_or_phone)
            except HTTPException:
                raise HTTPException(
                    status_code=400, detail="Login Credentials do not match"
                )
        else:
            raise HTTPException(
                status_code=400, detail="Login Credentials do not match"
            )

    if not user.is_active or not user.can_login:
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    if not verify_password(password, str(user.password_hash)):
        # check whether it's a temp password
        temp_password = str(user.temp_password_hash)
        if temp_password == "None":
            raise HTTPException(
                status_code=400, detail="Login Credentials do not match"
            )

        if temp_password and verify_password(password, temp_password):
            user.password_hash = temp_password
            user.temp_password_hash = ""
            await cu.db.commit()
            return schemas.UserSchema.model_validate(user)
        raise HTTPException(status_code=400, detail="Login Credentials do not match")

    return schemas.UserSchema.model_validate(user)


async def request_password_reset_otp(
    cu: CrudUtil,
    password_reset: schemas.PasswordResetRequest,
) -> dict[str, Any]:
    if password_reset.email:
        return await request_password_reset_otp_by_email(cu, password_reset.email)

    if password_reset.phone:
        return await request_password_reset_otp_by_phone(cu, password_reset.phone)

    raise HTTPException(status_code=403, detail="Email or phone is required")


async def request_password_reset_otp_by_email(
    cu: CrudUtil,
    email: str,
) -> dict[str, Any]:
    # check if the email exists, raise an exception if it doesn't
    db_user = await get_user_by_email(cu, email)

    # check if the user is_active and can login
    # raise an exception if not
    await is_valid_user(cu, db_user)

    return await async_send_otp_to_email(email)


async def request_password_reset_otp_by_phone(
    cu: CrudUtil,
    phone: str,
) -> dict[str, Any]:
    # check if the phone exists, raise an exception if it doesn't
    db_user = await get_user_by_phone(cu, phone)

    # check if the user is_active and can login
    # raise an exception if not
    await is_valid_user(cu, db_user)

    return await async_send_otp_to_phone(phone)


async def verify_password_reset_otp(
    cu: CrudUtil,
    otp_verify: schemas.PasswordResetVerifyOTP,
) -> dict[str, Any]:
    if otp_verify.email:
        return await verify_password_reset_otp_by_email(
            cu, otp_verify.email, otp_verify.otp
        )

    if otp_verify.phone:
        return await verify_password_reset_otp_by_phone(
            cu, otp_verify.phone, otp_verify.otp
        )

    raise HTTPException(status_code=403, detail="Email or phone is required")


async def verify_password_reset_otp_by_email(
    cu: CrudUtil,
    email: str,
    otp: str,
) -> dict[str, Any]:
    # check if the email exists, raise an exception if it doesn't
    db_user = await get_user_by_email(cu, email)

    # check if the user is_active and can login
    # raise an exception if not
    await is_valid_user(cu, db_user)

    # verify the OTP
    await async_verify_email_otp(email, otp)

    access_token = get_password_reset_access_token(db_user)

    return {"detail": "OTP verified successfully", "access_token": access_token}


async def verify_password_reset_otp_by_phone(
    cu: CrudUtil,
    phone: str,
    otp: str,
) -> dict[str, Any]:
    # check if the phone exists, raise an exception if it doesn't
    db_user = await get_user_by_phone(cu, phone)

    # check if the user is_active and can login
    # raise an exception if not
    await is_valid_user(cu, db_user)

    # verify the OTP
    await async_verify_phone_otp(phone, otp)

    access_token = get_password_reset_access_token(db_user)

    return {"detail": "OTP verified successfully", "access_token": access_token}


def get_password_reset_access_token(
    user: models.User,
) -> str:
    token_data = {
        "data": {
            "uuid": str(user.uuid),
            "email": str(user.email),
            "user_group": user.groups[0].name if user.groups else None,
        }
    }

    token = get_access_token(token_data)
    return token.access_token


async def reset_password(
    cu: CrudUtil,
    password_reset: schemas.PasswordReset,
    user: schemas.UserSchema,
) -> dict[str, Any]:
    # change the password at the db level
    return await change_user_password(cu, password_reset.password_or_pin, user)


async def change_own_password(
    cu: CrudUtil,
    password_change: schemas.PasswordChangeRequest,
    user: schemas.UserSchema,
) -> dict[str, Any]:
    # get the user, or raise exception
    db_user: models.User = await cu.get_model_or_404(
        model_to_get=models.User, model_conditions={"uuid": user.uuid}
    )

    password_hash: str = db_user.password_hash

    # check if the old password is correct
    if not verify_password(password_change.current_password, password_hash):
        raise HTTPException(status_code=403, detail="current password is incorrect")

    # change the password
    db_user.password_hash = get_password_hash(password_change.new_password)

    # commit the changes
    await cu.db.commit()
    return {"detail": "Password changed successfully. Please login again."}


async def list_admin_users(
    cu: CrudUtil, filter_: schemas.AdminUserFilter, skip: int = 0, limit: int = 100
) -> schemas.UserList:
    conditions = filter_.model_dump(exclude_unset=True, exclude={"user_group_name"})
    conditions["is_admin"] = True

    db_result: dict[str, Any] = await cu.list_model(
        model_to_list=models.User,
        list_conditions=conditions,
        skip=skip,
        limit=limit,
    )

    if filter_.user_group_name:

        def filter_user_group(user: models.User) -> bool | Any:
            if user.groups:
                return user.groups[0].name == filter_.user_group_name

            return False

        db_result["items"] = list(filter(filter_user_group, db_result["items"]))  # type: ignore
        return schemas.UserList(**db_result)

    return schemas.UserList(**db_result)


async def change_admin_password(
    cu: CrudUtil,
    user_uuid: str,
) -> schemas.PasswordChangeOut:
    db_user: models.User = await cu.get_model_or_404(
        model_to_get=models.User, model_conditions={"uuid": user_uuid}
    )
    password = gen_random_password()
    hashed_password = get_password_hash(password)

    db_user.temp_password_hash = hashed_password  # type: ignore
    await cu.db.commit()
    # send_change_password_mail(str(db_user.email), password)
    return schemas.PasswordChangeOut(password=password)


async def change_user_password(
    cu: CrudUtil,
    password: str,
    user: schemas.UserSchema,
) -> dict[str, str]:
    db_user: models.User = await cu.get_model_or_404(
        model_to_get=models.User, model_conditions={"uuid": user.uuid}
    )
    hashed_password = get_password_hash(password)

    db_user.password_hash = hashed_password
    await cu.db.commit()
    return {"detail": "Password changed successfully. Please login again."}


async def check_phone_availability(
    cu: CrudUtil,
    phone: str,
) -> dict[str, str]:
    # check if a phone number already exists
    # if it does, raise an exception, otherwise return True
    user: models.User | None = await cu.get_model_or_none(models.User, {"phone": phone})

    if user:
        raise HTTPException(status_code=403, detail="Phone number already exists")

    return {"status": "Phone number is available"}


async def is_existing_email(
    cu: CrudUtil,
    email: str,
) -> bool:
    # check if is valid existing email
    db_user: models.User | None = await cu.get_model_or_none(
        models.User, {"email": email}
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="No user found with this email")

    return True


async def is_existing_phone(
    cu: CrudUtil,
    phone: str,
) -> bool:
    # check if is valid existing phone
    db_user: models.User | None = await cu.get_model_or_none(
        models.User, {"phone": phone}
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="No user found with this phone")

    return True


async def is_valid_user(
    cu: CrudUtil,
    user: models.User,
) -> bool:
    # check if is valid existing user
    db_user: models.User | None = await cu.get_model_or_none(
        models.User, {"uuid": user.uuid}
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="No user found")

    if not db_user.can_login or not db_user.is_active:
        raise HTTPException(
            status_code=403, detail="User is not active or cannot login"
        )

    return True

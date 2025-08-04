#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-10 23:42:49
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


import re
from secrets import randbits, token_urlsafe
from datetime import datetime, timezone, timedelta, date
from random import choice as choose
from typing import Any
from twilio.rest import Client

from fastapi import HTTPException
from app.mixins.commons import DateRange
from pathlib import Path
import requests
import calendar
from passlib import pwd
import ulid
from asyncer import asyncify

from app.config.config import settings


def gen_email(mail_str: str = "") -> str:
    mail_str = mail_str or gen_random_str()
    mail_str = mail_str.replace("_", ".").replace("-", ".")
    return f"{mail_str}@diacyber.com"


def gen_random_password() -> str:
    return token_urlsafe(12)


def gen_random_business_id() -> str:
    return f"EXISTING-{gen_random_number(32)}"


def gen_random_str() -> str:
    rand_str: str = f"{pwd.genphrase(10)}_{pwd.genphrase(10)}"  # type: ignore
    return rand_str


def gen_random_name() -> str:
    return f"UNALLOCATED-{gen_random_number(8)}"


def gen_registration_number() -> str:
    return f"UNAVAILABLE-{gen_random_number(8)}"


def gen_random_vehicle_plate() -> str:
    # a sample plate number: ABJ-123AA
    first_part = pwd.genphrase(5)[:3].upper()  # type: ignore
    second_part = pwd.genphrase(5)[:2].upper()  # type: ignore
    number_part = randbits(10) + 1
    return f"{first_part}-{number_part}{second_part}"


def gen_random_date(start_date: date | None = None) -> date:
    days = [*range(-90, 1)]
    if start_date:
        return start_date + timedelta(days=choose([*range(90)]))

    return date.today() + timedelta(days=choose(days))


def get_txn_id() -> str:
    # return token_hex(8).upper()
    return ulid.ulid()


def gen_random_uuid() -> str:
    return ulid.ulid()


def gen_random_nin() -> int:
    return randbits(32)


# generate random number
def gen_random_number(bits: int = 16) -> int:
    return randbits(bits) + 1


def gen_random_phone() -> str:
    phone = f"{randbits(37)}"
    if len(phone) < 11:
        phone = f"{phone}{'1' * (11 - len(phone))}"
    if len(phone) > 11:
        phone = f"{phone[:11]}"
    return f"4134{phone}"


def gen_mobile_otp(number: str) -> dict[Any, Any]:
    phone_number: str = normalize_phone(number)

    resp = requester(
        f"{settings.sendchamp_base_url}/verification/create",
        method="post",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.sendchamp_key}",
        },
        json={
            "channel": "sms",
            "sender": "Sendchamp",
            "token_type": "numeric",
            "token_length": settings.otp_length,
            "expiration_time": settings.otp_life_span,
            "customer_mobile_number": phone_number,
            "meta_data": "",
        },
    )

    if resp.status_code != 200:
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code, detail=resp.json().get("message")
            )

    return resp.json()


def verify_mobile_otp(otp: str, reference: str) -> dict[Any, Any]:
    resp = requester(
        f"{settings.sendchamp_base_url}/verification/confirm",
        method="post",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.sendchamp_key}",
        },
        json={"verification_code": otp, "verification_reference": reference},
    )

    if resp.status_code != 200:
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code, detail=resp.json().get("message")
            )

    return resp.json()


def send_sms(phone: str, message: str) -> Any:
    if settings.sms_sender == "sendchamp":
        return send_champ_sms(phone, message)

    if settings.sms_sender == "twilio":
        return send_twilio_sms(phone, message)


def send_champ_sms(phone: str, message: str) -> dict[Any, Any]:
    phone_number: str = normalize_phone(phone)

    resp = requester(
        f"{settings.sendchamp_base_url}/sms/send",
        method="post",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.sendchamp_key}",
        },
        json={
            "to": [phone_number],
            "message": message,
            "sender_name": "Sendchamp",
            "route": "dnd",
        },
    )

    if resp.status_code != 200:
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code, detail=resp.json().get("message")
            )

    return resp.json()


def send_twilio_sms(phone: str, message: str) -> None:
    phone_number: str = normalize_phone(phone, intl=True)
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    message = client.messages.create(
        from_=settings.twilio_phone_number,
        to=phone_number,
        body=message,  # type: ignore
    )


async def async_send_twilio_sms(phone: str, message: str) -> None:
    return await asyncify(send_twilio_sms)(phone, message)


def send_twilio_sms_otp(phone: str) -> str | None:
    phone_number: str = normalize_phone(phone, intl=True)
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        verification = client.verify.v2.services(
            settings.deterrence_verify_service_sid,
        ).verifications.create(to=phone_number, channel="sms")

        return verification.sid
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=403,
            detail="Unable to send OTP. Please try again.",
        )


async def async_send_twilio_sms_otp(phone: str) -> str | None:
    return await asyncify(send_twilio_sms_otp)(phone)


def verify_twilio_sms_otp(phone: str, otp: str) -> bool:
    phone_number: str = normalize_phone(phone, intl=True)
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        verification_check = client.verify.v2.services(
            settings.deterrence_verify_service_sid,
        ).verification_checks.create(to=phone_number, code=otp)

        if verification_check.status != "approved":
            raise HTTPException(
                status_code=403,
                detail="Invalid OTP. Please try again.",
            )

        return True

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=403,
            detail="Invalid OTP. Please try again.",
        )


async def async_verify_twilio_sms_otp(phone: str, otp: str) -> bool:
    return await asyncify(verify_twilio_sms_otp)(phone, otp)


def send_twilio_email_otp(email: str) -> str | None:
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        verification = client.verify.v2.services(
            settings.deterrence_verify_service_sid,
        ).verifications.create(to=email.lower(), channel="email")

        return verification.sid

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=403,
            detail="Unable to send OTP. Please try again.",
        )


async def async_send_twilio_email_otp(email: str) -> str | None:
    return await asyncify(send_twilio_email_otp)(email)


def verify_twilio_email_otp(email: str, otp: str) -> bool:
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        verification_check = client.verify.v2.services(
            settings.deterrence_verify_service_sid,
        ).verification_checks.create(to=email.lower(), code=otp)

        if verification_check.status != "approved":
            raise HTTPException(
                status_code=401,
                detail="Invalid OTP. Please try again.",
            )

        return True

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=403,
            detail="Unable to verify OTP. Please try again.",
        )


async def async_verify_twilio_email_otp(email: str, otp: str) -> bool:
    return await asyncify(verify_twilio_email_otp)(email, otp)


def send_otp_to_phone(
    phone: str,
) -> dict[str, str]:
    # send otp to the phone number
    if not send_twilio_sms_otp(phone):
        raise HTTPException(
            status_code=403,
            detail="Unable to send OTP. Please try again.",
        )

    return {"status": "OTP sent to phone number"}


async def async_send_otp_to_phone(
    phone: str,
) -> dict[str, str]:
    # send otp to the phone number
    if not await async_send_twilio_sms_otp(phone):
        raise HTTPException(
            status_code=403,
            detail="Unable to send OTP. Please try again.",
        )

    return {"status": "OTP sent to phone number"}


def verify_phone_otp(
    phone: str,
    otp: str,
) -> dict[str, str]:
    # verify the otp
    if not verify_twilio_sms_otp(phone, otp):
        raise HTTPException(
            status_code=403,
            detail="Invalid OTP. Please try again.",
        )

    return {"status": "OTP verified"}


async def async_verify_phone_otp(
    phone: str,
    otp: str,
) -> dict[str, str]:
    # verify the otp
    if not await async_verify_twilio_sms_otp(phone, otp):
        raise HTTPException(
            status_code=403,
            detail="Invalid OTP. Please try again.",
        )

    return {"status": "OTP verified"}


def send_otp_to_email(
    email: str,
) -> dict[str, str]:
    # send otp to the email
    if not send_twilio_email_otp(email):
        raise HTTPException(
            status_code=403,
            detail="Unable to send OTP. Please try again.",
        )

    return {"status": "OTP sent to email"}


async def async_send_otp_to_email(
    email: str,
) -> dict[str, str]:
    # send otp to the email
    if not await async_send_twilio_email_otp(email):
        raise HTTPException(
            status_code=403,
            detail="Unable to send OTP. Please try again.",
        )

    return {"status": "OTP sent to email"}


def verify_email_otp(
    email: str,
    otp: str,
) -> dict[str, str]:
    # verify the otp
    if not verify_twilio_email_otp(email, otp):
        raise HTTPException(status_code=403, detail="Invalid OTP. Please try again.")

    return {"status": "OTP verified"}


async def async_verify_email_otp(
    email: str,
    otp: str,
) -> dict[str, str]:
    # verify the otp
    if not await async_verify_twilio_email_otp(email, otp):
        raise HTTPException(status_code=403, detail="Invalid OTP. Please try again.")

    return {"status": "OTP verified"}


def normalize_phone(phone: str, intl: bool = False) -> str:
    if intl:
        return f"+234{phone[-10:]}"

    return f"234{phone[-10:]}"


def denormalize_phone(phone: str) -> str:
    if phone.startswith("234"):
        return f"0{phone[3:]}"

    if phone.startswith("+234"):
        return f"0{phone[4:]}"

    if len(phone) == 11 and phone.startswith("0"):
        return phone

    return f"0{phone}" if len(phone) < 11 else phone


def currency(amount: float) -> float:
    return amount * 100


def get_current_date() -> str:
    today = datetime.now(timezone(timedelta(hours=1)))
    return today.strftime("%Y-%m-%d")


def get_current_time() -> str:
    now = datetime.now(timezone(timedelta(hours=1)))
    return now.strftime("%I:%M:%S")


def date_diff(date1: date, date2: date) -> int:
    result = date1 - date2
    return result.days


def time_diff(time1: str, time2: str, format: str = "%I:%M:%S") -> int:
    time_diff = datetime.strptime(time1, format) - datetime.strptime(time2, format)
    return time_diff.seconds


def date_days_add(date: date, days: int) -> date:
    return date + timedelta(days=days)


def get_today_date_range(column_name: str) -> DateRange:
    return DateRange(
        column_name=column_name, from_date=date.today(), to_date=date.today()
    )


def requester(
    url: str,
    method: str = "get",
    files: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> requests.Response:
    with requests.Session() as s:
        response: requests.Response = getattr(s, method)(
            url, files=files, data=data, json=json, headers=headers
        )

    return response


def get_last_str_number_part(number: str) -> int:
    search_result = re.search(r"\d+$", number)
    if not search_result:
        raise ValueError("string does not contain a number")

    return int(search_result.group())


def get_filename_from_path(path: str) -> str:
    return Path(path).name


def days_summary(days: int) -> str:
    if days == 0:
        return ""

    if days == 1:
        return f"{days} day"

    if days < 7:
        return f"{days} days"

    if days == 7:
        return f"{days // 7} week"

    if days < 30:
        return f"{days // 7} weeks {days_summary(days % 7)}"

    if days == 30:
        return f"{days // 30} month"

    if days < 365:
        return f"{days // 30} months {days_summary(days % 30)}"

    if days == 365:
        return f"{days // 365} year"

    return f"{days // 365} years {days_summary(days % 365)}"


def number_of_weekday_btw_dates(day_name: str, from_date: date, to_date: date) -> int:
    day_mapping = {
        "monday": calendar.MONDAY,
        "tuesday": calendar.TUESDAY,
        "wednesday": calendar.WEDNESDAY,
        "thursday": calendar.THURSDAY,
        "friday": calendar.FRIDAY,
        "saturday": calendar.SATURDAY,
        "sunday": calendar.SUNDAY,
    }

    target_date = day_mapping[day_name.lower()]
    one_day = timedelta(days=1)
    count = 0

    while from_date <= to_date:
        if from_date.weekday() == target_date:
            count += 1
        from_date += one_day

    return count


def find_perms() -> list[str]:
    app_dir = Path().cwd()

    perms: list[str] = []

    for router_file in app_dir.rglob("router.py"):
        with open(router_file, "r") as file:
            for line in file:
                perm_line = re.findall(r"HasPermission.+", line)
                if perm_line:
                    perms.extend(re.findall(r"\w+:\w+", perm_line[0]))

    return list(set(perms))


def make_filename(prefix: str = ""):
    moment = datetime.now().isoformat()[:19].replace("T", "_").replace(":", "-")
    return f"Data-Export_{moment}" if not prefix else f"{prefix}_{moment}"

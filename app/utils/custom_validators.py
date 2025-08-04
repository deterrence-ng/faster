#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-06-22 06:52:50
# @Author  : Dahir Muhammad Dahir
# @Description : something cool

import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional
from annotated_types import Gt, Le
from fastapi.exceptions import HTTPException
from pydantic import AfterValidator, condecimal, IPvAnyAddress, IPvAnyNetwork


# convert from naira to kobo, as all
# values in database should be in kobo
# convert from naira to kobo, as all
# values in database should be in kobo
def currency_in(amount: Decimal | None) -> Decimal | None:
    if amount is not None:
        return amount * 100

    return None


# convert from kobo back to naira
def currency_out(amount: Decimal | None) -> Decimal | None:
    if amount is not None:
        return amount / 100

    return None


def val_phone_number(value: str) -> str:
    # make sure number starts with 0 and
    # exactly 11 digits, and composed of
    # only numbers
    if value.startswith("0") and len(value) == 11 and value.isdigit():
        return value

    raise HTTPException(403, detail="Invalid phone number")


def make_uppercase(value: str | None) -> str | None:
    if value is not None:
        return value.upper()
    return None


def make_lowercase(value: str | None) -> str | None:
    if value is not None:
        return value.lower()
    return None


def make_capitalize(value: str | None) -> str | None:
    if value is not None:
        wordlist = [i.capitalize() for i in value.split()]

        return " ".join(wordlist)


def reg_number_out(value: str) -> str:
    if "UNAVAILABLE" in value:
        return "UNAVAILABLE"

    return value


def check_is_18_above(value: date) -> date | None:
    if not value:
        return None

    if date.today().year - value.year < 18:
        raise HTTPException(403, detail="Age must 18 years or above to register")

    return value


def clean_string(value: str) -> Optional[str]:
    if value is not None:
        return (
            value.replace(" ", "")
            .replace("-", "")
            .replace("_", "")
            .replace("/", "")
            .replace("\\", "")
            .upper()
        )

    return None


def val_domain(value: str) -> str:
    # Simple regex for domain/subdomain validation
    if re.match(r"^(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$", value):
        return value
    raise ValueError("Invalid domain or subdomain")


def val_asset(value: str) -> str:
    try:
        val_domain(value)
        return value
    except Exception:
        pass

    # Check if it's a valid IP address
    try:
        IPvAnyAddress(value)  # type: ignore
        return value
    except ValueError:
        pass

    # Check if it's a valid CIDR notation
    try:
        IPvAnyNetwork(value)  # type: ignore
        return value
    except ValueError:
        pass

    raise ValueError(
        "Invalid asset identifier. Must be a valid domain, CIDR, URL or IP address."
    )


UpStr = Annotated[str, AfterValidator(make_uppercase)]
LowStr = Annotated[str, AfterValidator(make_lowercase)]
CapStr = Annotated[str, AfterValidator(make_capitalize)]
RegOut = Annotated[str, AfterValidator(reg_number_out)]
PositiveDecimal = condecimal(ge=0)
Money = Annotated[Decimal, "Money"]
Phone = Annotated[str, AfterValidator(val_phone_number)]
Port = Annotated[int, Gt(-1), Le(65535), "Port"]
LegalBirthdate = Annotated[date | None, AfterValidator(check_is_18_above)]
CleanStr = Annotated[str | None, AfterValidator(clean_string)]
Domain = Annotated[str, AfterValidator(val_domain)]
IPAddress = Annotated[IPvAnyAddress, "IPAddress"]
IPNetwork = Annotated[IPvAnyNetwork, "IPNetwork"]
ScopeAsset = Annotated[str, AfterValidator(val_asset)]

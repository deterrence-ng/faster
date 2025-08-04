#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-08 18:05:48
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


from enum import Enum


class ActionStatus(str, Enum):
    success = "success"
    failed = "failed"


class Gender(str, Enum):
    male = "m"
    female = "f"
    na = "NA"


class FileFormat(str, Enum):
    pdf = ".pdf"
    excel = ".xlsx"
    csv = ".csv"
    json = ".json"
    xml = ".xml"


class LicenseValidity(str, Enum):
    valid = "valid"
    expired = "expired"


class UserStatus(str, Enum):
    enabled = "enabled"
    disabled = "disabled"

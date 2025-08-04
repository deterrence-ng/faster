#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-07 12:40:32
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


from app.utils.misc import send_sms


def send_account_creation_sms(
    phone_number: str, username: str, password: str, firstname: str
) -> None:
    message = f"Hello {firstname}, your account has been approved and created successfully. You can login with your phone number: {username} as username and your password is: {password} at https://faster.diacyber.com/signin"
    send_sms(phone_number, message)


def send_password_change_sms(
    phone_number: str, username: str, password: str, firstname: str
) -> None:
    message = f"Hello {firstname}, your password has been changed successfully. You can login with your phone number: {username} as username and your new password is: {password} at https://faster.diacyber.com/signin"
    send_sms(phone_number, message)


def test_sms(phone_number: str, message: str) -> None:
    send_sms(phone_number, message)

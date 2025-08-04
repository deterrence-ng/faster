#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2024-10-17 09:37:43
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production Settings"""

    app_name: str = "faster"
    environment: str = ""

    # production database settings
    prod_db_user: str
    prod_db_password: str
    prod_db: str
    prod_db_host: str
    prod_db_port: int
    prod_db_url_async: str
    prod_db_url_sync: str

    # local database settings
    local_db_user: str
    local_db_password: str
    local_db: str
    local_test_db: str
    local_db_host: str
    local_db_port: str
    local_db_url_async: str
    local_db_url_sync: str

    # test database settings
    test_db_url: str

    # database connection pool settings
    database_pool_size: int = 50
    database_max_overflow: int = 85

    # Test Admin User
    test_super_user_email: str
    test_super_username: str
    test_super_user_password: str

    # Initial Admin User (only for local runs)
    initial_email: str
    initial_password: str
    initial_firstname: str
    initial_lastname: str
    initial_middlename: str

    # jwt settings
    jwt_secret_key: str
    jwt_algorithm: str
    token_life_span: int
    token_mobile_life_span: int
    token_long_life_span: int

    # OTP
    otp_life_span: int
    otp_length: int

    # url
    token_url: str
    frontend_url: str
    backend_url: str

    # email
    source_email: str
    sendgrid_api_key: str

    # SMS
    sendchamp_base_url: str
    sendchamp_key: str

    # Phone
    source_phone: str

    # cloud
    cloud_bucket_name: str
    cloud_storage_url: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    # cors
    cors_origins: list[str] = []

    # Twilio API
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    deterrence_verify_service_sid: str

    # Active SMS Sender
    # Options: "sendchamp", "twilio"
    sms_sender: str

    # System Variables
    super_user_id: str

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.staging", ".env.production"),
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore

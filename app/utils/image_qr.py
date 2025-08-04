#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-23 23:47:33
# @Author  : Dahir Muhammad Dahir
# @Description : something cool


import base64
import datetime
import io
from typing import Any
import ulid

from app.config.config import settings
from app.utils.misc import requester
from fastapi.datastructures import UploadFile
import qrcode
from io import BytesIO
from qrcode import constants
from google.cloud import run_v2
from google.cloud import storage
from PIL import Image, ImageDraw, ImageFont


def create_frontend_qr_data(unique_data: str, frontend_var_name: str = "") -> str:
    frontend_qr_url = settings.frontend_url
    return f"{frontend_qr_url}{unique_data}"


def create_qr_file(
    data: str, fill_color: str = "black", back_color: str = "white"
) -> Image.Image | Any:
    qr = qrcode.QRCode(  # type: ignore
        version=None, error_correction=constants.ERROR_CORRECT_M, box_size=10, border=1
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color=fill_color, back_color=back_color)
    return image


def upload_base64_image_to_cloud(
    base64_image: str,
    filename: str,
    cloud_bucket_name: str = settings.cloud_bucket_name,
):
    in_memory_image = get_in_memory_from_base64(base64_image)
    if upload_file_to_cloud(in_memory_image, filename, cloud_bucket_name):
        return f"{settings.cloud_storage_url}/{cloud_bucket_name}/{filename}"

    raise Exception("Unable to upload image to cloud")


def get_in_memory_from_base64(base64_image: str):
    to_decode = base64_image.replace("\n", "").replace(" ", "").replace("\\n", "")
    try:
        decoded_image = Image.open(io.BytesIO(base64.b64decode(to_decode)))
    except Exception:
        raise Exception("Invalid base64 image")

    in_memory = BytesIO()
    decoded_image.save(in_memory, "PNG")
    in_memory.seek(0)
    in_memory_png = in_memory.getvalue()
    return in_memory_png


def generate_in_memory_file(qr_image: Image.Image | Any) -> bytes:
    in_memory = BytesIO()
    qr_image.save(in_memory, "PNG")
    in_memory.seek(0)
    in_memory_png = in_memory.getvalue()
    return in_memory_png


def resize_image(
    uploaded_file: UploadFile, new_size: tuple[int, int] = (350, 466)
) -> Image.Image:
    image = Image.open(uploaded_file.file)
    image_out = image.resize(new_size)
    return image_out


def get_image(image_bytes: BytesIO) -> Image.Image:
    return Image.open(image_bytes)


def upload_file_to_cloud(
    in_memory_file: bytes,
    file_name: str,
    bucket_name: str,
    subfolder: str = "",
) -> bool:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    img_name = f"{file_name}"
    blob = bucket.blob(f"{subfolder}{img_name}")

    blob.upload_from_string(in_memory_file, content_type="image/png")
    return True


def create_and_upload_qr_cloud(
    qr_unique_data: str,
    qr_filename: str,
    qr_display_text: str = "",
) -> bool:
    qr_data = qr_unique_data
    qr_image = create_qr_file(qr_data)

    if qr_display_text:
        qr_image = add_qr_display_text(qr_image, qr_display_text)

    in_memory_image = generate_in_memory_file(qr_image)
    bucket_name = settings.cloud_bucket_name
    return upload_file_to_cloud(
        in_memory_image, qr_filename, bucket_name, subfolder="qr-codes/"
    )


def add_qr_display_text(
    qr_image: Image.Image,
    qr_display_text: str,
) -> Image.Image:
    qr_image = qr_image.convert("RGB")
    width, height = qr_image.size
    new_image = Image.new("RGB", (width, height + 100), (255, 255, 255))
    text_image = Image.new("RGB", (width, 100), (255, 255, 255))
    font = ImageFont.truetype("app/assets/fonts/Roboto.ttf", size=42)
    draw = ImageDraw.Draw(text_image)
    draw.text(
        (width / 2, 100 / 2), qr_display_text, font=font, anchor="mm", fill=(0, 0, 0)
    )
    new_image.paste(qr_image, (0, 0))
    new_image.paste(text_image, (0, height))
    return new_image


def upload_image_to_cloud(
    image: Image.Image,
    cloud_bucket_var_name: str,
    file_name: str,
    subfolder: str = "",
) -> str:
    in_memory_image = generate_in_memory_file(image)
    bucket_name = settings.cloud_bucket_name

    if upload_file_to_cloud(in_memory_image, file_name, bucket_name, subfolder):
        return f"{settings.cloud_storage_url}/{bucket_name}/{subfolder}{file_name}"

    raise Exception("Unable to upload image to cloud")


def upload_remote_image_to_cloud(url: str, filename: str, bucket_var_name: str) -> str:
    response = requester(url)
    image = get_image(io.BytesIO(response.content))
    return upload_image_to_cloud(image, bucket_var_name, filename)


def upload_image_file_to_cloud(
    image_file: UploadFile,
    subfolder: str = "",
    cloud_bucket_var_name: str = "",
    resize: bool = True,
) -> str:
    resized_image = resize_image(image_file) if resize else Image.open(image_file.file)
    file_name = f"{ulid.ulid()}.png"
    return upload_image_to_cloud(
        resized_image, cloud_bucket_var_name, file_name, subfolder
    )


# upload file to bucket and return the url,
# the file can only be pdf, png, jpeg. The file
# will be convert to in memory file and uploaded
def upload_any_file_to_cloud(
    file: UploadFile,
    file_name: str,
    subfolder: str = "",
    cloud_bucket_name: str = settings.cloud_bucket_name,
) -> str:
    if file.content_type in ["image/png", "image/jpeg", "image/jpg"]:
        image = Image.open(file.file)
        return upload_image_to_cloud(image, cloud_bucket_name, file_name, subfolder)

    if file.content_type in ["application/pdf"]:
        in_memory_file = file.file.read()
        return export_in_memory_file_to_cloud(
            in_memory_file, file_name, "application/pdf", cloud_bucket_name, subfolder
        )

    raise Exception("Invalid file type")


# file types are like
# for png: image/png
# for jpeg: image/jpeg
# for excel: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
# for pdf: application/pdf
# for xml: application/xml
# for json: application/json
# for csv: text/csv
# for txt: text/plain
# for binary: application/octet-stream
def export_in_memory_file_to_cloud(
    in_memory_file: bytes,
    file_name: str,
    file_type: str = "image/png",
    cloud_bucket_name: str = settings.cloud_bucket_name,
    subfolder: str = "",
) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(cloud_bucket_name)
    blob = bucket.blob(f"{subfolder}{file_name}")

    blob.upload_from_string(in_memory_file, content_type=file_type)
    return f"{settings.cloud_storage_url}/{cloud_bucket_name}/{subfolder}{file_name}"


def generate_signed_url_v4(bucket_name: str, file_name: str) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=24),
        method="GET",
    )

    return url


def generate_upload_signed_url_v4(bucket_name: str, file_name: str) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=24),
        method="PUT",
    )

    return url


def run_cloud_job(job_name: str) -> bool:
    # create a client
    client = run_v2.JobsClient()

    # initialize request
    request = run_v2.RunJobRequest(
        name=job_name,
    )

    # make the request
    client.run_job(request=request)

    # wait for the operation to complete
    print("Waiting for operation to complete...")

    return True


def configure_storage_cors() -> None:
    if settings.environment != "production":
        return

    bucket_name = settings.cloud_bucket_name

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    bucket.cors = [
        {
            "origin": [f"{settings.frontend_url}"],
            "responseHeader": [
                "Access-Control-Allow-Origin",
                "Content-Type",
                "x-goog-resumable",
            ],
            "method": ["GET", "PUT", "POST"],
            "maxAgeSeconds": 3600 * 24 * 7,
        }
    ]

    bucket.patch()

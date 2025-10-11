from typing import BinaryIO
from fastapi import UploadFile


def file_to_upload_file(file: BinaryIO, filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=file)

from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from storages.backends.s3boto3 import S3Boto3Storage
import logging
import re
from rest_framework import serializers
from minsirx.settings import MEDIA_ROOT

logger = logging.getLogger(__name__)
class MediaStorage(S3Boto3Storage):
    bucket_name = os.environ.get("BUCKETNAME")
    location = 'media'
    file_overwrite = True

class StaticStorage(S3Boto3Storage):
    bucket_name = os.environ.get("BUCKETNAME")
    location = 'static'

def __get_storage_class():
    if os.environ.get("OS_ENV") == "PROD":
        media_storage_class = MediaStorage
    else:
        media_storage_class = FileSystemStorage
    return media_storage_class

class OverwriteStorage(__get_storage_class()):
    def get_available_name(self, name, max_length=None):
        if os.environ.get("OS_ENV") != "PROD":
            if self.exists(name):
                os_temp_path = os.path.join(MEDIA_ROOT, name)
                os.remove(os_temp_path)
        return name
    
def custom_upload_to(instance, filename):
    path_name = f"{type(instance).__name__}_images"
    image_number = 0
    image_name = instance.id
    if image_name is None:
        return f'{path_name}/' + f"{filename}"
    new_file_name = os.path.basename(instance.image.path)
    base, extension = os.path.splitext(new_file_name)
    file_name = f"{image_name}_{image_number}{extension}"
    if instance.image:
        # If instance already has an image, get its filename
        existing_filename = instance.image_url
        if existing_filename:
            existing_filename, ext = os.path.splitext(existing_filename)
            # File with same name already exists
            exstng_image_number = existing_filename.split("_")[1]
            exstng_image_number = int(exstng_image_number)
            image_number = exstng_image_number+1
            file_name = f"{image_name}_{image_number}{extension}"
    return f'{path_name}/' + f"{file_name}"
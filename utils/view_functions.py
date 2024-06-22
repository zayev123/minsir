from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from base64 import b64decode
import os
from cryptography.fernet import Fernet
# nano general_funcs/myStorage.py
def decodeImage(data):
    try:
        data = b64decode(data.encode('UTF-8'))
        buf = BytesIO(data)
        return buf
    except:
        return None

def createPostWithImage(mySerialized, myObject, imgName):
    imgCheck = False
    if 'base64Image' in mySerialized.validated_data and mySerialized.validated_data['base64Image']!= None and mySerialized.validated_data['base64Image']!= '' and 'imageType' in mySerialized.validated_data:
        if mySerialized.validated_data['imageType'] == 'PNG':
            ext = ".png"
            contentType = 'image/png'
        elif mySerialized.validated_data['imageType'] == 'JPEG':
            ext = ".jpg"
            contentType = 'image/jpeg'

        imgCheck = True
        img = decodeImage(mySerialized.validated_data['base64Image'])

    mySerialized.validated_data['base64Image'] = ''
    mySerialized.save()
    copy = mySerialized.data

    if imgCheck:
        myImage = InMemoryUploadedFile(img, field_name=None, name=imgName + str(
            mySerialized.data['id']) + "bckt_id" + ext, content_type=contentType, size=img.tell, charset=None)
        myObject.image = myImage
        myObject.save(update_fields=['image'])
        copy['image'] = myObject.image.url

    return copy


def putWithImage(mySerialized, myObject, imgName):
    if 'base64Image' in mySerialized.validated_data and mySerialized.validated_data['base64Image']!= None and mySerialized.validated_data['base64Image']!= '' and 'imageType' in mySerialized.validated_data:
        if mySerialized.validated_data['imageType'] == 'PNG':
            ext = ".png"
            contentType = 'image/png'
        elif mySerialized.validated_data['imageType'] == 'JPEG':
            ext = ".jpg"
            contentType = 'image/jpeg'

        img = decodeImage(mySerialized.validated_data['base64Image'])
        myObject.image = InMemoryUploadedFile(img, field_name=None, name=imgName + str(
            myObject.id) + "bckt_id" + ext, content_type=contentType, size=img.tell, charset=None)

    mySerialized.validated_data['base64Image'] = ''
    mySerialized.save()
    srData = mySerialized.data

    return srData

def get_key_from_env():
    # Get the key from the environment variable
    key_str = os.environ.get("TEMP_ACCOUNT_KEY")
    if not key_str:
        raise ValueError("Encryption key not found in environment variables")
    return key_str.encode()

def encrypt_value(value):
    key = get_key_from_env()
    f = Fernet(key)
    encrypted_value = f.encrypt(value.encode())
    return encrypted_value

def decrypt_value(encrypted_value):
    key = get_key_from_env()
    f = Fernet(key)
    decrypted_value = f.decrypt(encrypted_value).decode()
    return decrypted_value
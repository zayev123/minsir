from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailOrPhoneNumberBackend(ModelBackend):
    def authenticate(self, request, email=None, phone_number=None, password=None, **kwargs):
        UserModel = get_user_model()

        if email:
            user = UserModel.objects.filter(email=email).first()
        elif phone_number:
            user = UserModel.objects.filter(phone_number=phone_number).first()
        else:
            return None

        if user and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
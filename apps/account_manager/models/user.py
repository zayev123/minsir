import os
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

from utils.storage_func import OverwriteStorage, custom_upload_to
from django.contrib.gis.db.models import PointField

# add number of contests allowed per game
class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, name=None, password=None, **extra_fields):
        # Create and return a regular user with an email or phone number
        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Create and return a superuser with an email
        return self.create_user(email=email, password=password, **extra_fields, is_admin=True)

# add number of contests allowed per game

class User(AbstractBaseUser):
    REQUIRED_FIELDS = ['name']
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        blank=True, 
        null=True,
    )
    phone = models.CharField(
        verbose_name='phone',
        max_length=255,
        unique=True,
        blank=True, 
        null=True,
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    nin = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(
        upload_to=custom_upload_to, blank=True, null=True, storage=OverwriteStorage())
    image_url = models.CharField(max_length=100, blank=True, null=True)
    base64Image = models.TextField(blank=True, null=True)
    imageType = models.CharField(max_length=10, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    location = PointField(geography=True, blank=True, null=True)
    objects = UserManager()
    digi6Code = models.CharField(max_length=6, blank=True, null=True)
    is6Code_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        is_created_new = False
        if self.pk is None:
            is_created_new = True
        super(User, self).save(*args, **kwargs)
        if not is_created_new:
            image_path = None
            if self.image:
                image_path = os.path.basename(self.image.path)
            if image_path != self.image_url:
                self.image_url = image_path
                super(User, self).save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def __str__(self):
        name = None
        if self.name is None:
            name = self.email
        if name is None:
            name = self.id
        return str(self.id) + ', ' + f"{name}"

    class Meta:
        verbose_name_plural = "       Users"
        db_table = 'users'
        ordering = ['id']

    @staticmethod
    def get_deleted_user():
        return User.objects.get_or_create(
            email= "deleted@gmail.com",
            name="deleted",
            phone="deleted",
        )[0]
import datetime
import random
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import FileExtensionValidator

from shared.models import BaseModel

SIMPLE, MANAGER, ADMIN = 'simple', 'manager', 'admin'
VIA_EMAIL, VIA_PHONE = 'email', 'phone'
NEW, CODE_VERIFIED, DONE, PHOTO_STEP = 'new', 'code_verified', 'done', 'photo_step'


class User(AbstractUser, BaseModel):
    GENDER_CHOICES = (
        ('female', 'female'),
        ('male', 'male')
    )
    USER_RULES = (
        (SIMPLE, SIMPLE),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN),
    )
    AUTH_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFIED, CODE_VERIFIED),
        (DONE, DONE),
        (PHOTO_STEP, PHOTO_STEP),
    )
    email = models.EmailField(max_length=50, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=13, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='users_photos/', null=True, blank=True,
                              validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic', 'heif'])])
    user_role = models.CharField(max_length=13, choices=USER_RULES, default=SIMPLE)
    auth_type = models.CharField(max_length=13, choices=AUTH_TYPE)
    auth_status = models.CharField(max_length=13, choices=AUTH_STATUS, default=NEW)

    def __str__(self):
        return self.username

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"

    def default_username(self):
        if not self.username:
            norm_username = f"instagram-{str(uuid.uuid4()).split('-')[-1]}"
            while User.objects.filter(username=norm_username):
                norm_username += str(range(1, 9))
            self.username = norm_username

    def check_email(self):
        if self.email:
            norm_email = str(self.email).lower()
            self.email = norm_email

    def default_password(self):
        if not self.password:
            norm_password = f"password-{str(uuid.uuid4()).split('-')[-1]}"
            self.password = norm_password

    def hash_password(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)

    def clean(self):
        self.default_username()
        self.default_password()
        self.check_email()
        self.hash_password()

    def save(self, *args, **kwargs):
        self.clean()
        super(User, self).save(*args, **kwargs)

    def create_verify_code(self, verify_type):
        code = ''.join([str(random.randint(1, 10) % 10) for _ in range(4)])
        user_confirmed = UserConfirmation.objects.filter(user_id=self.id)
        if user_confirmed:
            user_confirmed.update(code=code, verify_type=verify_type)
            if verify_type == VIA_PHONE:
                user_confirmed.update(expiration_time=datetime.datetime.now() + datetime.timedelta(minutes=2))
            elif verify_type == VIA_EMAIL:
                user_confirmed.update(expiration_time=datetime.datetime.now() + datetime.timedelta(minutes=2))
        else:
            UserConfirmation.objects.create(
                user_id=self.id,
                code=code,
                verify_type=verify_type
            ).save()
        return code

    def token(self):
        token = RefreshToken.for_user(self)
        return {
            'access': str(token.access_token),
            'refresh': str(token)
        }


class UserConfirmation(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='verify_code')
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=13, choices=VERIFY_TYPE)
    expiration_time = models.DateTimeField()
    is_confirmation = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        elif self.verify_type == VIA_PHONE:
            self.expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
        super(UserConfirmation, self).save(*args, **kwargs)

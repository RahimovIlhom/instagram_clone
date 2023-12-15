from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_phone, send_email, check_auth_type
from .models import User, VIA_EMAIL, VIA_PHONE, CODE_VERIFIED, DONE, PHOTO_STEP


class SignUpSerializers(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True, required=False)
    auth_status = serializers.CharField(read_only=True, required=False)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializers, self).__init__(*args, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['id', 'auth_type', 'auth_status']

    def create(self, validated_data):
        user = super(SignUpSerializers, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user, code)
            # send_phone(user, code)
        else:
            data = {
                'success': False,
                'message': 'Email yoki telefon raqam xato'
            }
            raise ValidationError(data)
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializers, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        email_or_phone = data.get('email_or_phone').lower()
        auth_type = check_email_or_phone(email_or_phone)
        if auth_type == 'email':
            data = {
                'email': data.get('email_or_phone'),
                'auth_type': VIA_EMAIL
            }
        elif auth_type == 'phone':
            data = {
                'phone_number': data.get('email_or_phone'),
                'auth_type': VIA_PHONE
            }
        return data

    def validate_email_or_phone(self, email_or_phone):
        email_or_phone = email_or_phone.lower()
        if User.objects.filter(email=email_or_phone):
            data = {
                'success': False,
                'message': "Bunday email mavjud"
            }
            raise ValidationError(data)
        elif User.objects.filter(phone_number=email_or_phone):
            data = {
                'success': False,
                'message': "Bunday telefon raqam mavjud"
            }
            raise ValidationError(data)
        return email_or_phone

    def to_representation(self, instance):
        data = super(SignUpSerializers, self).to_representation(instance)
        data.update(instance.token())
        return data


class UserInfoUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        password = data.get('password', None)
        password_confirm = data.get('password_confirm', None)
        if password != password_confirm:
            data = {
                'success': False,
                'message': "Parollaringiz mos emas!"
            }
            raise ValidationError(data)
        if password:
            validate_password(password)
        return data

    def validate_username(self, username):
        if len(username) <= 4 or len(username) > 15:
            data = {
                'success': False,
                'message': 'Username xatolik'
            }
            raise ValidationError(data)
        else:
            if username.isdigit():
                data = {
                    'success': False,
                    'message': "Foydalanuvchi nomi sonlar bo'lmasligi kerak!"
                }
                raise ValidationError(data)
            user = User.objects.filter(username=username)
            if user:
                data = {
                    'success': False,
                    'message': 'Bunday foydalanuvchi nomli foydalanuvchi mavjud'
                }
                raise ValidationError(data)
        return username

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)

        if instance.password:
            instance.set_password(validated_data.get('password'))
        if instance.auth_status in (CODE_VERIFIED, DONE, PHOTO_STEP):
            instance.auth_status = DONE
        else:
            data = {
                'success': False,
                'message': 'Sizga ruxsat yo\'q'
            }
            raise ValidationError(data)

        instance.save()
        return instance


class UserPhotoChangeSerializer(serializers.Serializer):
    photo = serializers.ImageField(write_only=True, required=False,
                                   validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic', 'heif'])])

    def update(self, instance, validated_data):
        instance.photo = validated_data.get('photo', None)
        if instance.auth_status in (DONE, PHOTO_STEP):
            instance.auth_status = PHOTO_STEP
        instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def validate(self, attrs):
        user = self.check_auth(attrs)
        data = {
            'success': True,
            'message': "Muvaffaqiyatli kirildi!",
            'user_role': user.user_role,
            'fullname': user.fullname,
            'auth_status': user.auth_status
        }
        data.update(user.token())
        return data

    @staticmethod
    def check_auth(data):
        user_input = data.get('userinput')
        auth_type = check_auth_type(user_input)
        if auth_type == 'email':
            username = LoginSerializer.get_user(email__iexact=user_input).username
        elif auth_type == 'phone':
            username = LoginSerializer.get_user(phone_number__iexact=user_input).username
        elif auth_type == 'username':
            username = LoginSerializer.get_user(username__iexact=user_input).username
        else:
            error = {
                'success': False,
                'message': "Email, telefon yoki foydalanuvchi nomi xato"
            }
            raise ValidationError(error)

        authenticate_kwargs = {
            'username': username,
            'password': data.get('password')
        }
        user = authenticate(**authenticate_kwargs)
        if user:
            return user
        else:
            raise ValidationError({
                'success': False,
                'message': "Parolingiz xat!o"
            })

    @staticmethod
    def get_user(**kwargs):
        users = User.objects.filter(**kwargs)
        if users:
            return users.first()
        else:
            data = {
                'success': False,
                'message': "Bunday foydalanuvchi mavjud emas!"
            }
            raise ValidationError(data)


class RefreshTokenSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data


class LogOutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        user = User.objects.filter(Q(email=email_or_phone) | Q(phone_number=email_or_phone))
        if not user:
            raise NotFound(detail="Foydalanuvchi topilmadi!")
        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False, read_only=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'password', 'confirm_password']

    def validate(self, attrs):
        password = attrs.get('password', None)
        confirm_password = attrs.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError({
                'success': False,
                'message': "parollaringiz mos emas!"
            })
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password')
        if password:
            instance.set_password(password)
        else:
            raise ValidationError({
                'success': False,
                'message': "Parol kiritilmadi!"
            })
        return super(ResetPasswordSerializer, self).update(instance, validated_data)


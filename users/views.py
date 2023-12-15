from django.utils.datetime_safe import datetime
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from shared.utility import send_email, check_email_or_phone
from .models import User, NEW, CODE_VERIFIED, VIA_EMAIL, VIA_PHONE, DONE
from .serializers import SignUpSerializers, UserInfoUpdateSerializer, UserPhotoChangeSerializer, LoginSerializer, \
    RefreshTokenSerializer, LogOutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = SignUpSerializers


class VerifyAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, *args, **kwargs):
        user = self.request.user
        self.check_user(user)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            # send_phone(user.phone_number, code)
            send_email(user.phone_number, code)
        else:
            data = {
                'success': False,
                'message': "Email yoki telefon raqa xato"
            }
            raise ValidationError(data)
        data = {
            'success': True,
            'auth_type': user.auth_type,
            'auth_status': user.auth_status,
        }
        data.update(user.token())
        return Response(data, status=200)

    @staticmethod
    def check_user(user):
        verifies = user.verify_code.filter(expiration_time__gte=datetime.now(), is_confirmation=False)
        if verifies:
            data = {
                'success': False,
                'message': "kod yuborilgan, biroz kuting"
            }
            raise ValidationError(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')
        self.check_verify_code(user, code)
        data = {
            'success': True,
            'message': "Verifikatsiyadan o'tidi!"
        }
        data.update(user.token())
        data.update({'auth_status': user.auth_status})
        return Response(data)

    @staticmethod
    def check_verify_code(user, code):
        verify = user.verify_code.filter(expiration_time__gte=datetime.now(), code=code)
        if not verify:
            data = {
                'success': False,
                'message': 'Kod yaroqsiz yoki xato'
            }
            raise ValidationError(data)
        verify.update(is_confirmation=True)
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True


class UserInfoUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserInfoUpdateSerializer
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(UserInfoUpdateView, self).update(request, *args, **kwargs)
        user = self.get_object()
        data = {
            'success': True,
            'message': "Ma'lumotlaringiz kiritildi!",
            'auth_status': user.auth_status
        }
        data.update(user.token())
        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        super(UserInfoUpdateView, self).partial_update(request, *args, **kwargs)
        user = self.get_object()
        data = {
            'success': True,
            'message': "Ma'lumotlaringiz kiritildi!",
            'auth_status': user.auth_status
        }
        data.update(user.token())
        return Response(data)


class UserPhotoUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserPhotoChangeSerializer
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(UserPhotoUpdateView, self).update(request, *args, **kwargs)
        user = self.get_object()
        data = {
            'success': True,
            'message': "Rasmingiz o'zgartirildi!",
            'auth_status': user.auth_status
        }
        data.update(user.token())
        return Response(data)


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer


class RefreshTokenView(TokenRefreshView):
    serializer_class = RefreshTokenSerializer


class LogOutView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        serializer = LogOutSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success': True,
                'message': "Siz tizimdan chiqdingiz!"
            }
            return Response(data, status=205)

        except TokenError:
            return Response(status=400)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny, ]
    serializer_class = ForgotPasswordSerializer

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        email_or_phone = serializer.validated_data.get('email_or_phone')
        if check_email_or_phone(email_or_phone) == 'phone':
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        elif check_email_or_phone(email_or_phone) == 'email':
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        else:
            data = {
                'success': False,
                'message': "Email yoki telefon raqam yuboring!"
            }
            raise ValidationError(data)
        return Response(data={
            'success': True,
            'message': "Email yoki telefon raqamingizga kod yuborildi",
            'access': user.token()['access'],
            'refresh': user.token()['refresh'],
        })


class ResetPasswordView(UpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ResetPasswordSerializer
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ResetPasswordView, self).update(request, *args, **kwargs)
        user = self.get_object()
        data = {
            'success': True,
            'message': "Parolingiz tiklandi!",
        }
        data.update(user.token())
        data['auth_status'] = user.auth_status
        return Response(data=data, status=200)

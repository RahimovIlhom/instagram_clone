from django.urls import path

from .views import SignUpView, VerifyAPIView, UserInfoUpdateView, UserPhotoUpdateView, LoginView, RefreshTokenView, \
    LogOutView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('signup/', SignUpView.as_view()),
    path('verify/', VerifyAPIView.as_view()),
    path('user-update/', UserInfoUpdateView.as_view()),
    path('user-photo-update/', UserPhotoUpdateView.as_view()),
    path('login/', LoginView.as_view()),
    path('login/refresh/', RefreshTokenView.as_view()),
    path('logout/', LogOutView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
]

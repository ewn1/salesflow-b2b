from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import MeView, RegisterView

urlpatterns = [
    # Login route: returns the access and refresh tokens
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # Route to renew an expired access token using the refresh token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Public registration route: creates a new user account
    path("register/", RegisterView.as_view(), name="register"),
    # Profile of the user that owns the access token
    path("me/", MeView.as_view(), name="me"),
]

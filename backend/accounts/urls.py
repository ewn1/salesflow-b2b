from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import RegisterView

urlpatterns = [
    # Rota para login: Retorna acces_token e refresh_token
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # Rota para renovar o access_token expirado usando o refresh_token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
]

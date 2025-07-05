from django.urls import path

from . import views

urlpatterns = [
    # Auth endpoints// api/auth/
    path('isauthenticated/', views.check_auth, name='is_authenticated'),
    path('user/register/', views.userRegister, name='user_register'),
    path('user/login/', view=views.userLogin, name='user_login'),
    path('user/logout/', view=views.userLogout, name='user_logout'),
    path('token/refresh/', view=views.cookieTokenRefresh, name='token_refresh'),
    path('google/', view=views.google_login, name='google-login'),
    # User endpoints
]

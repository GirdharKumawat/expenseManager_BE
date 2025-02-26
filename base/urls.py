 
from django.urls import path ,include
from . import views

urlpatterns = [ 
    path('', view=views.getRoutes),
    path('api/auth/', include('account.urls')),
]

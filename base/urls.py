 
from django.urls import path ,include
from . import views

urlpatterns = [ 
    path('', view=views.getRoutes),
    path('api/auth/', include('account.urls')),
    path('api/add/expense/',view=views.addExpense),
    path('api/get/expenses/',view=views.getExpenses),
    path('api/get/expenses/<str:pk>/',view=views.getExpenses),
    path('api/delete/expense/<str:pk>/',view=views.deleteExpense),
     
]

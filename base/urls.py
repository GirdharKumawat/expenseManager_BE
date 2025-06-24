from django.urls import path, include
from . import views

urlpatterns = [
    # Base route
    path('', views.getRoutes),
    
    # Authentication routes
    path('api/auth/', include('account.urls')),
    
    # User profile routes
    path('api/profile/', views.getProfile),
    
    # Expense management routes
    path('api/add/expense/', views.addExpense),
    path('api/get/expenses/', views.getExpenses),
    path('api/get/expenses/<str:pk>/', views.getExpenses),
    path('api/delete/expense/<str:pk>/', views.deleteExpense),
]

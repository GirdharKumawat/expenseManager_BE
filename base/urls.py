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
    
    path('api/createGroup/',view=views.createGroup),
    path('api/addGroupMember/',view=views.addGroupMember),
    path('api/addGroupExpense/',view=views.addGroupExpense),
    
    path('api/getGroups/',view=views.getGroups),
    
    path('api/deleteGroup/<str:group_id>/',view=views.deleteGroup),
    path('api/removeGroupMember/',view=views.removeGroupMember),
    path('api/deleteGroupExpense/<str:expense_id>/',view=views.deleteGroupExpense),
    
]

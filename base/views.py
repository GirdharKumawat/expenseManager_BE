from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
import os
from  . models import Expense
from  . serializers import ExpenseSerializer
BaseUrl = os.getenv('BASE_URL')

@api_view(['GET'])
def getRoutes(request):
    Routes = {
        'Token': BaseUrl+'api/auth/token/',
        'Token Refresh': BaseUrl+'api/auth/token/refresh/',
        'User Ragister': BaseUrl+'api/auth/user/ragister/',
        'User Login': BaseUrl+'api/auth/user/login/',
        'add Expense': BaseUrl+'api/add/expense/',
        'get Expenses': BaseUrl+'api/get/expenses/',
        'get ExpenseByCategory': BaseUrl+'api/get/expensebycategory/',
        'delete Expense': BaseUrl+'api/delete/expense/<str:pk >/',
        
   }
    return Response(Routes)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addExpense(request):
    serializer = ExpenseSerializer(data = request.data) 
    if serializer.is_valid():
        user = request.user
        amount = serializer.validated_data['amount']
        category = serializer.validated_data['category']
        description = serializer.validated_data['description']
        expense = Expense(user=user, amount=amount, category=category, description=description)
        expense.save()  
    else:
        return Response(serializer.errors)
    
    return Response({"msg":'Expense added'}, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getExpenses(request):
    user = request.user
    expenses = user.expenses.all()    
    serializer = ExpenseSerializer(expenses, many=True)
    return Response({"data" :serializer.data})
  

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def getExpenseByCategory(request):
    user = request.user
    category = request.data['category']
    expenses = user.expenses.filter(category=category)
    serializer = ExpenseSerializer(expenses, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deleteExpense(request,pk):
    user = request.user
    expense = user.expenses.get(id=pk)
    expense.delete()
    return Response('Expense deleted')


# sample data
# {
#     "amount": 100,
#     "category": "FOOD",
#     "description": "Bought some food"
# }
# {
#     "amount": 200,
#     "category": "TRANSPORT",
#     "description": "Took a cab"
# }
# 

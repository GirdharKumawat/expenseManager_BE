import os
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import Expense
from  . serializers import ExpenseSerializer
from django.utils.timezone import now
BaseUrl = os.getenv('BASE_URL')


@api_view(['GET'])
def getRoutes(request):
    
    print("BaseUrl", BaseUrl)
    Routes = {
        'Token': BaseUrl+'api/auth/token/',
        'Token Refresh': BaseUrl+'api/auth/token/refresh/',
        'User Ragister': BaseUrl+'api/auth/user/ragister/',
        'User Login': BaseUrl+'api/auth/user/login/',
        'User Profilr': BaseUrl+'api/profile/',
        'add Expense': BaseUrl+'api/add/expense/',
        'get Expenses': BaseUrl+'api/get/expenses/pk/',
        'delete Expense': BaseUrl+'api/delete/expense/pk/',

   }
    return Response(Routes)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])       
def getProfile(request):
    user = request.user
    profile = {
        'username': user.username,
        'email': user.email,  
    }
    return Response(profile ,status=200)
  
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addExpense(request):
    serializer = ExpenseSerializer(data = request.data) 
    if serializer.is_valid():
        user = request.user
        amount = serializer.validated_data['amount']
        category = serializer.validated_data['category']
        description = serializer.validated_data['description']
        date = serializer.validated_data.get('date', now().date())
        paymentType = serializer.validated_data['paymentType']
        expense = Expense(user=user, amount=amount, category=category, description=description,date = date,paymentType=paymentType)
        expense.save()  
    else:
        return Response(serializer.errors)
    
    res = {
        "msg":{'Expense added',},
        "data" : { 
            "amount":amount,
            "category":category,
            "description":description,
            "date" :expense.date,
            "paymentType":paymentType,
            "id":expense.id,
            }
           }
    return Response(res, status=201)
 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getExpenses(request, pk=""):
    user = request.user
    expenses = user.expenses.all()
    if pk and pk.strip():
        expenses = expenses.filter(category=pk)
    serializer = ExpenseSerializer(expenses, many=True)
    data = reversed(serializer.data)
    return Response({"data": data}, status=200)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteExpense(request,pk):
    user = request.user
    expense = user.expenses.get(id=pk)
    expense.delete()
    return Response('Expense deleted')

 
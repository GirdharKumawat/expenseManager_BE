import os
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes , authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Expense
from .serializers import ExpenseSerializer
from django.utils.timezone import now
from account.authentication import CookieJWTAuthentication

BASE_URL = os.getenv('BASE_URL', '')


@api_view(['GET'])
def getRoutes(request):
    """
    List all available API endpoints.
    """
    routes = {
        'Token': BASE_URL + 'api/auth/token',
        'Token Refresh': BASE_URL + 'api/auth/token/refresh',
        'User Register': BASE_URL + 'api/auth/user/register',
        'User Login': BASE_URL + 'api/auth/user/login',
        'User Profile': BASE_URL + 'api/profile',
        'Add Expense': BASE_URL + 'api/add/expense',
        'Get Expenses': BASE_URL + 'api/get/expenses/pk',
        'Get Expenses By Category': BASE_URL + 'api/get/expenses/category',
        'Delete Expense': BASE_URL + 'api/delete/expense/pk',
    }
    return Response(routes, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([CookieJWTAuthentication])
def getProfile(request):
    """
    Retrieve the profile of the authenticated user.
    """
    user = request.user
    profile = {
        'username': user.username,
        'email': user.email,
    }
    return Response({'data': profile}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([CookieJWTAuthentication])
def addExpense(request):
    """
    Add a new expense for the authenticated user.
    """
    serializer = ExpenseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    user = request.user
    amount = serializer.validated_data['amount']
    category = serializer.validated_data['category']
    description = serializer.validated_data['description']
    date = serializer.validated_data.get('date', now().date())
    payment_type = serializer.validated_data['paymentType']
    
    expense = Expense(
        user=user,
        amount=amount,
        category=category,
        description=description,
        date=date,
        paymentType=payment_type
    )
    expense.save()
    
    response_data = {
        "message": "Expense added successfully",
        "data": {
            "id": expense.id,
            "amount": amount,
            "category": category,
            "description": description,
            "date": expense.date,
            "paymentType": payment_type,
        }
    }
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def getExpenses(request, pk=""):

    user = request.user
    expenses = user.expenses.all()
    
    if pk and pk.strip():
        expenses = expenses.filter(category=pk)
        
    serializer = ExpenseSerializer(expenses, many=True)
    data = list(reversed(serializer.data))
    
    return Response({"data": data}, status=status.HTTP_200_OK)

 

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([CookieJWTAuthentication])
def deleteExpense(request, pk):
    """
    Delete an expense by its ID.
    """
    user = request.user
    try:
        expense = user.expenses.get(id=pk)
        expense.delete()
        return Response(
            {"message": "Expense deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    except Expense.DoesNotExist:
        return Response(
            {"error": "Expense not found"},
            status=status.HTTP_404_NOT_FOUND
        )


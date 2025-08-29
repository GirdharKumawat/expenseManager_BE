import os
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes , authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Expense ,GroupExpense,GroupMember,ExpenseGroup,GroupExpenseShare
from django.contrib.auth.models import User
from .serializers import ExpenseSerializer ,GroupExpenseSerializer,ExpenseGroupSerializer,GroupExpenseShareSerializer
from django.utils.timezone import now
from account.authentication import CookieJWTAuthentication
from .group_summary import build_group_summary,get_group_detail
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
    
    expenses = expenses.order_by('-date')  # Sort by date descending (newest first)
    serializer = ExpenseSerializer(expenses, many=True)
    data = serializer.data

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

#----------------------------------------------------

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def createGroup(request):
    """
    Create a group and add the creator as a member.
    """
    serializer = ExpenseGroupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    group = serializer.save(created_by=request.user)
    GroupMember.objects.create(group=group, user=request.user)
    
    newGroup = get_group_detail(group.id,request.user.id)
    return Response({'message': 'Group created', 'data': serializer.data, 'group':newGroup},status=status.HTTP_201_CREATED)

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def addGroupMember(request):
    """
    Add an existing user to a group.
    """
    group_id = request.data.get("group_id")
    user_email = request.data.get("email")

    # Step 1: Validate group
    try:
        group = ExpenseGroup.objects.get(id=group_id)
    except ExpenseGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

    # Step 2: Validate user
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Step 3: Prevent duplicate member
    if GroupMember.objects.filter(group=group, user=user).exists():
        return Response({'error': 'User is already a member of the group'}, status=status.HTTP_400_BAD_REQUEST)

    # Step 4: Create group member
    GroupMember.objects.create(group=group, user=user)
    
    newGroup = get_group_detail(group_id,request.user.id)

    return Response({'message': f"{user.username} added to group '{group.name}'",'group':newGroup}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def addGroupExpense(request):
    """
    Add an expense to a group and distribute shares.
    """
    group_id = request.data.get("group")
    paidBy_id = request.data.get("paidBy")
    shares_data = request.data.get("shares")

    # Step 1: Validate existence
    try:
        group = ExpenseGroup.objects.get(id=group_id)
    except ExpenseGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        user = User.objects.get(id=paidBy_id)
    except ExpenseGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

    # Step 2: Validate and save expense
    expense_serializer = GroupExpenseSerializer(data=request.data)
    if not expense_serializer.is_valid():
        return Response({'error': expense_serializer.   errors}, status=status.HTTP_400_BAD_REQUEST)

    expense = expense_serializer.save(paid_by=user)

    # Step 3: Save each share
    for share in shares_data:
        participant_id = share.get("participant_id")
        share_amount = share.get("share_amount")

        try:
            participant = User.objects.get(id=participant_id)
            GroupExpenseShare.objects.create(
                expense=expense,
                participant=participant,
                share_amount=share_amount
            )
        except User.DoesNotExist:
            continue  # Skip invalid user, optionally log it
        
        newGroup = get_group_detail(group_id,request.user.id)

    return Response({
        'message': 'Group expense added successfully',
        'expense': GroupExpenseSerializer(expense).data,
        'group':newGroup
    }, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def getGroups(request):
    user = request.user
    try:
        data = build_group_summary(user)
        return Response({"data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in getGroups: {e}")
        return Response({"error": "Something went wrong while fetching groups."}, status=500)


@api_view(['DELETE'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteGroup(request, group_id):
    try:
        group = ExpenseGroup.objects.get(id=group_id)
    except ExpenseGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)

    # Optional: Only allow creator to delete
    if group.created_by != request.user:
        return Response({'error': 'You are not allowed to delete this group'}, status=403)

    group.delete()
    return Response({'message': 'Group deleted successfully'}, status=204)

@api_view(['DELETE'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def removeGroupMember(request):
    group_id = request.data.get("group_id")
    user_id = request.data.get("user_id")

    try:
        member = GroupMember.objects.get(group_id=group_id, user_id=user_id)
        member.delete()
        return Response({'message': 'Member removed successfully'}, status=204)
    except GroupMember.DoesNotExist:
        return Response({'error': 'Member not found in this group'}, status=404)

@api_view(['DELETE'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteGroupExpense(request, expense_id):
    try:
        expense = GroupExpense.objects.get(id=expense_id)
    except GroupExpense.DoesNotExist:
        return Response({'error': 'Expense not found'}, status=404)

    # Optional: Only allow the person who paid to delete
    if expense.paid_by != request.user:
        return Response({'error': 'You can only delete expenses you paid'}, status=403)

    expense.delete()
    return Response({'message': 'Group expense deleted successfully'}, status=204)

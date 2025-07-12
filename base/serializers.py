from rest_framework import serializers
from .models import Expense ,GroupExpense,GroupMember,ExpenseGroup,GroupExpenseShare
from account.serializers import UserSerializer
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'amount', 'category', 'description','paymentType', 'date']
        read_only_fields = ['id']
        

class ExpenseGroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = ExpenseGroup
        fields = ['id', 'name', 'description', 'created_by', 'created_at']


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user']
        

class GroupExpenseShareSerializer(serializers.ModelSerializer):
    participant = UserSerializer(read_only=True)

    class Meta:
        model = GroupExpenseShare
        fields = ['id', 'expense', 'participant', 'share_amount']


class GroupExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    shares = GroupExpenseShareSerializer(many=True, read_only=True)

    class Meta:
        model = GroupExpense
        fields = ['id', 'group', 'title', 'amount', 'paid_by', 'paid_on', 'notes', 'shares']

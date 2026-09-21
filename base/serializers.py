from decimal import Decimal
from rest_framework import serializers
from .models import Expense ,GroupExpense,GroupMember,ExpenseGroup,GroupExpenseShare
from account.serializers import UserSerializer
class ExpenseSerializer(serializers.ModelSerializer):
    transaction_type = serializers.CharField(required=False, default='DEBIT')

    class Meta:
        model = Expense
        fields = ['id', 'amount', 'category', 'description', 'paymentType', 'date', 'transaction_type']
        read_only_fields = ['id']


class TransactionSyncItemSerializer(serializers.ModelSerializer):
    client_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    transaction_type = serializers.ChoiceField(choices=Expense.TRANSACTION_TYPE_CHOICES, default='DEBIT')
    category = serializers.ChoiceField(choices=Expense.CATEGORY_CHOICES)
    paymentType = serializers.ChoiceField(choices=Expense.paymentType_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Expense
        fields = ['id', 'client_id', 'amount', 'category', 'description', 'paymentType', 'date', 'transaction_type']
        read_only_fields = ['id']

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.copy()
            # Normalize category case-insensitively
            if 'category' in data and isinstance(data['category'], str):
                val = data['category'].strip()
                for choice, _ in Expense.CATEGORY_CHOICES:
                    if choice.lower() == val.lower():
                        data['category'] = choice
                        break

            # Normalize paymentType / payment_type case-insensitively
            p_val = data.get('paymentType') or data.get('payment_type')
            if p_val and isinstance(p_val, str):
                p_val_str = str(p_val).strip()
                for choice, _ in Expense.paymentType_CHOICES:
                    if choice.lower() == p_val_str.lower():
                        data['paymentType'] = choice
                        break

            # Normalize transaction_type
            if 'transaction_type' in data and isinstance(data['transaction_type'], str):
                data['transaction_type'] = data['transaction_type'].strip().upper()

        return super().to_internal_value(data)


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

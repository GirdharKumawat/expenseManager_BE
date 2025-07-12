from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Expense(models.Model):
    # Define category choices
    CATEGORY_CHOICES = [
        ('Food', 'Food'), 

        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Utilities', 'Utilities'),
        ('Shopping', 'Shopping'),
        ('Health', 'Health'),
        ('Rent', 'Rent'),
        ('Other', 'Other'),
    ]
    paymentType_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile', 'Mobile'),
        ('Bank', 'Bank'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)  # Use choices here
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=now)
    paymentType = models.CharField(max_length=100, choices=paymentType_CHOICES)  # Use choices here

    def __str__(self):
        return f"{self.category} - {self.amount}"
    
class ExpenseGroup(models.Model):
    name = models.CharField(max_length=50)
    description =models.TextField(blank=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class GroupMember(models.Model):
    group = models.ForeignKey(ExpenseGroup,on_delete=models.CASCADE,related_name='membership')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memeberships')
    
    class Meta:
        unique_together = ('group','user')
    
    def __str__(self):
        return f"{self.user.username} in {self.group.name}"
    
class GroupExpense(models.Model):
    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='paid_expenses')
    paid_on = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"
 
class GroupExpenseShare(models.Model):
    expense = models.ForeignKey(GroupExpense, on_delete=models.CASCADE, related_name='shares')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_shares')
    share_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('expense', 'participant')

    def __str__(self):  
        return f"{self.participant.username} owes ₹{self.share_amount}"




    
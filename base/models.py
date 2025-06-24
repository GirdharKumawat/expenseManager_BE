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
    
from django.contrib import admin
from . import models

admin.site.register(models.Expense)

admin.site.register(models.ExpenseGroup)

admin.site.register(models.GroupMember)

admin.site.register(models.GroupExpense)

admin.site.register(models.GroupExpenseShare)

 


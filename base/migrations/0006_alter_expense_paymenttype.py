# Generated by Django 5.1.5 on 2025-04-18 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_remove_expense_mode_expense_paymenttype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='paymentType',
            field=models.CharField(choices=[('Cash', 'Cash'), ('Card', 'Card'), ('Mobile', 'Mobile'), ('Bank', 'Bank')], max_length=100),
        ),
    ]

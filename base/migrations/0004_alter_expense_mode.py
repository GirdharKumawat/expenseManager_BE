# Generated by Django 5.1.5 on 2025-04-14 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_expense_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='mode',
            field=models.CharField(choices=[('Cash', 'Cash'), ('Card', 'Card'), ('Bank', 'Bank'), ('Mobile', 'Mobile')], default='Cash', max_length=100),
        ),
    ]

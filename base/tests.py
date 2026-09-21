from django.test import TestCase
from django.contrib.auth.models import User
from base.models import Expense
from base.statement_parser import parse_statement_file, infer_category_and_type, extract_transaction_details
import io

class StatementParserTests(TestCase):
    def test_extract_transaction_details_regex(self):
        desc, merchant, ref, ptype = extract_transaction_details("UPI/DR/425912345678/SWIGGY BANGALORE/HDFC/pay")
        self.assertEqual(merchant, "Swiggy Bangalore")
        self.assertEqual(ref, "425912345678")
        self.assertEqual(ptype, "Mobile")

        desc, merchant, ref, ptype = extract_transaction_details("UPI/CR/987654321012/JOHN DOE/ICICI/pay")
        self.assertEqual(merchant, "John Doe")
        self.assertEqual(ref, "987654321012")
        self.assertEqual(ptype, "Mobile")

        desc, merchant, ref, ptype = extract_transaction_details("POS 456789 DECATHLON SPORTS STORE")
        self.assertEqual(merchant, "Decathlon Sports Store")
        self.assertEqual(ptype, "Card")

    def test_infer_category_and_type(self):
        cat, ttype = infer_category_and_type("Paid to Swiggy Food")
        self.assertEqual(cat, "Food")
        self.assertEqual(ttype, "DEBIT")

        cat, ttype = infer_category_and_type("Salary Credited for Sept")
        self.assertEqual(cat, "Salary")
        self.assertEqual(ttype, "CREDIT")

        cat, ttype = infer_category_and_type("Uber Ride to Office")
        self.assertEqual(cat, "Transport")
        self.assertEqual(ttype, "DEBIT")

    def test_csv_statement_parser(self):
        csv_content = (
            "Date,Description,Debit,Credit,Balance\n"
            "15-09-2026,UPI/DR/425912345678/SWIGGY/HDFC,250.00,,14750.00\n"
            "16-09-2026,UPI/CR/425987654321/ACME SALARY/ICICI,,50000.00,64750.00\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        results = parse_statement_file(file_obj, "test.csv")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['transaction_type'], 'DEBIT')
        self.assertEqual(results[0]['amount'], 250.00)
        self.assertEqual(results[0]['payee_merchant'], 'Swiggy')
        self.assertEqual(results[0]['reference_id'], '425912345678')
        self.assertEqual(results[0]['balance'], 14750.00)

        self.assertEqual(results[1]['transaction_type'], 'CREDIT')
        self.assertEqual(results[1]['amount'], 50000.00)
        self.assertEqual(results[1]['payee_merchant'], 'Acme Salary')
        self.assertEqual(results[1]['reference_id'], '425987654321')
        self.assertEqual(results[1]['balance'], 64750.00)

class ExpenseModelTests(TestCase):
    def test_create_credit_and_debit_expense(self):
        user = User.objects.create_user(username="testuser", password="password123")
        expense_debit = Expense.objects.create(
            user=user,
            amount=100.0,
            category="Food",
            description="Lunch",
            paymentType="Cash",
            transaction_type="DEBIT"
        )
        expense_credit = Expense.objects.create(
            user=user,
            amount=1000.0,
            category="Salary",
            description="Monthly Pay",
            paymentType="Bank",
            transaction_type="CREDIT"
        )
        self.assertEqual(expense_debit.transaction_type, "DEBIT")
        self.assertEqual(expense_credit.transaction_type, "CREDIT")


from rest_framework.test import APIClient
from rest_framework import status

class TransactionSyncTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="syncuser", email="sync@example.com", password="password123")
        self.client.force_authenticate(user=self.user)

    def test_sync_transactions_success_array(self):
        payload = [
            {
                "client_id": "tx-001",
                "amount": 250.50,
                "category": "Food",
                "description": "Swiggy Order",
                "paymentType": "Card",
                "transaction_type": "DEBIT",
                "date": "2026-09-15"
            },
            {
                "client_id": "tx-002",
                "amount": 50000.00,
                "category": "Salary",
                "description": "Monthly Salary",
                "paymentType": "Bank",
                "transaction_type": "CREDIT",
                "date": "2026-09-01"
            }
        ]
        response = self.client.post('/api/transactions/sync', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['summary']['synced_count'], 2)
        self.assertEqual(response.data['summary']['duplicate_count'], 0)
        self.assertEqual(response.data['summary']['failed_count'], 0)
        self.assertEqual(len(response.data['synced']), 2)
        self.assertEqual(response.data['synced'][0]['client_id'], 'tx-001')
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 2)

    def test_sync_transactions_dict_payload(self):
        payload = {
            "transactions": [
                {
                    "client_id": "tx-101",
                    "amount": 120.00,
                    "category": "Transport",
                    "description": "Cab fare",
                    "paymentType": "Mobile",
                    "transaction_type": "DEBIT",
                    "date": "2026-09-18"
                }
            ]
        }
        response = self.client.post('/api/transactions/sync', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['summary']['synced_count'], 1)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

    def test_sync_transactions_deduplication(self):
        # Pre-create an expense
        Expense.objects.create(
            user=self.user,
            amount=150.00,
            category="Food",
            description="Coffee",
            paymentType="Cash",
            transaction_type="DEBIT",
            date="2026-09-19"
        )

        payload = [
            # Exact duplicate of existing DB record
            {
                "client_id": "tx-dup-1",
                "amount": 150.00,
                "category": "Food",
                "description": "Coffee",
                "paymentType": "Cash",
                "transaction_type": "DEBIT",
                "date": "2026-09-19"
            },
            # New transaction
            {
                "client_id": "tx-new-1",
                "amount": 450.00,
                "category": "Shopping",
                "description": "T-Shirt",
                "paymentType": "Card",
                "transaction_type": "DEBIT",
                "date": "2026-09-19"
            },
            # Duplicate item repeated inside the same batch
            {
                "client_id": "tx-new-1-repeat",
                "amount": 450.00,
                "category": "Shopping",
                "description": "T-Shirt",
                "paymentType": "Card",
                "transaction_type": "DEBIT",
                "date": "2026-09-19"
            }
        ]

        response = self.client.post('/api/transactions/sync', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['summary']['synced_count'], 1)
        self.assertEqual(response.data['summary']['duplicate_count'], 2)
        self.assertEqual(len(response.data['duplicates']), 2)
        # Total DB expenses should now be 2 (1 initial + 1 newly synced)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 2)

    def test_sync_transactions_case_normalization(self):
        payload = [
            {
                "amount": 300.00,
                "category": "food", # lowercase category
                "paymentType": "card", # lowercase paymentType
                "transaction_type": "debit", # lowercase type
                "date": "2026-09-19"
            }
        ]
        response = self.client.post('/api/transactions/sync', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['summary']['synced_count'], 1)
        expense = Expense.objects.get(user=self.user)
        self.assertEqual(expense.category, "Food")
        self.assertEqual(expense.paymentType, "Card")
        self.assertEqual(expense.transaction_type, "DEBIT")

    def test_sync_transactions_validation_error(self):
        payload = [
            {
                "client_id": "tx-err-1",
                "amount": -50.00, # Invalid amount
                "category": "InvalidCategory",
                "paymentType": "Cash"
            }
        ]
        response = self.client.post('/api/transactions/sync', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['synced_count'], 0)
        self.assertEqual(response.data['summary']['failed_count'], 1)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertEqual(response.data['errors'][0]['client_id'], 'tx-err-1')

    def test_sync_transactions_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/transactions/sync', [], format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



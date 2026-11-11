import datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Expense
from .utils import predict_category


class SmartExpenseTrackerTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create primary test user
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice'
        )
        # Create second test user to verify user data isolation
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob'
        )

        today = timezone.localdate()
        # Create expenses for alice
        self.exp1 = Expense.objects.create(
            user=self.user1,
            description='Uber ride to university',
            amount=Decimal('15.50'),
            category='Travel',
            date=today,
            notes='Midterm exam commute'
        )
        self.exp2 = Expense.objects.create(
            user=self.user1,
            description='Pizza lunch with friends',
            amount=Decimal('24.00'),
            category='Food',
            date=today,
            notes='Dominoes personal pan'
        )
        # Create expense for bob
        self.exp_bob = Expense.objects.create(
            user=self.user2,
            description='Electricity bill payment',
            amount=Decimal('95.00'),
            category='Bills',
            date=today,
            notes='Monthly utility bill'
        )

    def test_smart_category_prediction(self):
        """Verify automatic keyword suggestions map correctly."""
        self.assertEqual(predict_category('Took an Uber to the train station'), 'Travel')
        self.assertEqual(predict_category('Bought pizza and coffee for lunch'), 'Food')
        self.assertEqual(predict_category('Paid electricity bill and internet wifi'), 'Bills')
        self.assertEqual(predict_category('Movie ticket and popcorn at cinema'), 'Entertainment')
        self.assertEqual(predict_category('Doctor consultation and cough syrup medicine'), 'Healthcare')
        self.assertEqual(predict_category('Purchased books and course tuition'), 'Education')
        self.assertEqual(predict_category('Random item without keywords'), 'Other')

    def test_user_authentication_flow(self):
        """Verify user login and redirection."""
        # Unauthenticated user visiting dashboard redirected to login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        # Login user1
        logged_in = self.client.login(username='alice', password='Password123!')
        self.assertTrue(logged_in)

        # Now dashboard loads successfully
        dash_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, 'Alice')
        self.assertContains(dash_response, 'Uber ride to university')

    def test_user_isolation(self):
        """Verify alice cannot see or modify bob's expenses."""
        self.client.login(username='alice', password='Password123!')

        # Dashboard should not contain Bob's expense
        dash_response = self.client.get(reverse('dashboard'))
        self.assertNotContains(dash_response, 'Electricity bill payment')

        # Expense list should only contain Alice's expenses
        list_response = self.client.get(reverse('expense_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.context['page_obj']), 2)
        self.assertNotContains(list_response, 'Electricity bill payment')

        # Alice trying to edit Bob's expense must return 404
        edit_response = self.client.get(reverse('edit_expense', kwargs={'pk': self.exp_bob.id}))
        self.assertEqual(edit_response.status_code, 404)

        # Alice trying to delete Bob's expense must return 404
        del_response = self.client.post(reverse('delete_expense', kwargs={'pk': self.exp_bob.id}))
        self.assertEqual(del_response.status_code, 404)
        # Verify Bob's expense still exists
        self.assertTrue(Expense.objects.filter(id=self.exp_bob.id).exists())

    def test_create_expense_validation(self):
        """Verify adding an expense with positive amount validation."""
        self.client.login(username='alice', password='Password123!')

        # Negative / zero amount should fail
        response = self.client.post(reverse('add_expense'), {
            'description': 'Invalid negative expense',
            'amount': '-10.00',
            'category': 'Other',
            'date': timezone.localdate().strftime('%Y-%m-%d'),
            'notes': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(description='Invalid negative expense').exists())

        # Valid expense creation
        valid_response = self.client.post(reverse('add_expense'), {
            'description': 'College tuition fee',
            'amount': '150.00',
            'category': 'Education',
            'date': timezone.localdate().strftime('%Y-%m-%d'),
            'notes': 'Fall semester installment'
        })
        self.assertEqual(valid_response.status_code, 302)
        new_exp = Expense.objects.get(description='College tuition fee')
        self.assertEqual(new_exp.user, self.user1)
        self.assertEqual(new_exp.amount, Decimal('150.00'))
        self.assertEqual(new_exp.category, 'Education')

    def test_edit_and_delete_expense(self):
        """Verify editing and deleting an expense."""
        self.client.login(username='alice', password='Password123!')

        # Edit exp1
        edit_response = self.client.post(reverse('edit_expense', kwargs={'pk': self.exp1.id}), {
            'description': 'Updated Uber ride to airport',
            'amount': '22.75',
            'category': 'Travel',
            'date': timezone.localdate().strftime('%Y-%m-%d'),
            'notes': 'Terminal 2 ride'
        })
        self.assertEqual(edit_response.status_code, 302)
        self.exp1.refresh_from_db()
        self.assertEqual(self.exp1.description, 'Updated Uber ride to airport')
        self.assertEqual(self.exp1.amount, Decimal('22.75'))

        # Delete exp1
        del_response = self.client.post(reverse('delete_expense', kwargs={'pk': self.exp1.id}))
        self.assertEqual(del_response.status_code, 302)
        self.assertFalse(Expense.objects.filter(id=self.exp1.id).exists())

    def test_expense_filters(self):
        """Verify time and category filters."""
        self.client.login(username='alice', password='Password123!')

        # Filter by category Travel
        res_travel = self.client.get(reverse('expense_list'), {'category': 'Travel'})
        self.assertEqual(res_travel.status_code, 200)
        self.assertContains(res_travel, 'Uber ride to university')
        self.assertNotContains(res_travel, 'Pizza lunch with friends')

        # Filter by today
        res_today = self.client.get(reverse('expense_list'), {'time_filter': 'today'})
        self.assertEqual(res_today.status_code, 200)
        self.assertEqual(res_today.context['filtered_count'], 2)

    def test_csv_and_pdf_reports(self):
        """Verify CSV and PDF downloads."""
        self.client.login(username='alice', password='Password123!')

        # CSV Export
        csv_res = self.client.get(reverse('export_csv'))
        self.assertEqual(csv_res.status_code, 200)
        self.assertTrue(csv_res['Content-Type'].startswith('text/csv'))
        self.assertIn('attachment; filename="smart_expenses_alice_', csv_res['Content-Disposition'])
        csv_content = csv_res.content.decode('utf-8')
        self.assertIn('Uber ride to university', csv_content)
        self.assertIn('Pizza lunch with friends', csv_content)
        self.assertNotIn('Electricity bill payment', csv_content)

        # PDF Export
        pdf_res = self.client.get(reverse('export_pdf'))
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="smart_expenses_alice_', pdf_res['Content-Disposition'])
        self.assertTrue(len(pdf_res.content) > 1000)
        self.assertTrue(pdf_res.content.startswith(b'%PDF'))

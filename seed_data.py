import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from expenses.models import Expense


class Command(BaseCommand):
    help = 'Populates the database with a demo user and realistic sample expenses for testing & demonstration.'

    def handle(self, *args, **options):
        # Create or fetch demo user
        demo_user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Alex',
                'last_name': 'Morgan'
            }
        )
        if created:
            demo_user.set_password('Demo1234!')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS('Created user: demo (Password: Demo1234!)'))
        else:
            self.stdout.write(self.style.WARNING('User demo already exists.'))

        today = timezone.localdate()

        sample_expenses = [
            # Today's expenses
            {
                'description': 'Starbucks coffee and croissant',
                'amount': Decimal('7.85'),
                'category': 'Food',
                'date': today,
                'notes': 'Morning coffee meeting'
            },
            {
                'description': 'Uber cab ride to client office',
                'amount': Decimal('18.40'),
                'category': 'Travel',
                'date': today,
                'notes': 'Downtown return trip'
            },
            # This week's expenses
            {
                'description': 'Grocery shopping at Trader Joes',
                'amount': Decimal('64.20'),
                'category': 'Food',
                'date': today - datetime.timedelta(days=1),
                'notes': 'Weekly fruits, veggies, and milk'
            },
            {
                'description': 'High-speed Fiber Internet bill',
                'amount': Decimal('59.99'),
                'category': 'Bills',
                'date': today - datetime.timedelta(days=2),
                'notes': 'Monthly broadband subscription'
            },
            {
                'description': 'Cinema tickets for Dune with friends',
                'amount': Decimal('28.50'),
                'category': 'Entertainment',
                'date': today - datetime.timedelta(days=3),
                'notes': 'IMAX 3D screening'
            },
            {
                'description': 'Petrol fuel refill at Shell',
                'amount': Decimal('42.00'),
                'category': 'Travel',
                'date': today - datetime.timedelta(days=4),
                'notes': 'Full tank unleaded'
            },
            # This month's expenses
            {
                'description': 'Monthly Apartment Electricity Bill',
                'amount': Decimal('84.50'),
                'category': 'Bills',
                'date': today - datetime.timedelta(days=8),
                'notes': 'Utility bill invoice #88412'
            },
            {
                'description': 'Pharmacy prescription medicines & vitamins',
                'amount': Decimal('35.25'),
                'category': 'Healthcare',
                'date': today - datetime.timedelta(days=11),
                'notes': 'Allergy medication'
            },
            {
                'description': 'Python & Django Web Course on Udemy',
                'amount': Decimal('19.99'),
                'category': 'Education',
                'date': today - datetime.timedelta(days=14),
                'notes': 'Full stack curriculum'
            },
            {
                'description': 'Nike Running Shoes purchase',
                'amount': Decimal('89.00'),
                'category': 'Shopping',
                'date': today - datetime.timedelta(days=16),
                'notes': 'Summer sale discount'
            },
            {
                'description': 'Dinner at Italian Trattoria',
                'amount': Decimal('52.30'),
                'category': 'Food',
                'date': today - datetime.timedelta(days=19),
                'notes': 'Pasta & dessert with family'
            },
            # Past months for monthly trend chart
            {
                'description': 'Doctor dental cleaning and checkup',
                'amount': Decimal('120.00'),
                'category': 'Healthcare',
                'date': today - datetime.timedelta(days=35),
                'notes': 'Annual checkup'
            },
            {
                'description': 'Water & Sewer utility bill',
                'amount': Decimal('45.00'),
                'category': 'Bills',
                'date': today - datetime.timedelta(days=40),
                'notes': 'City utilities'
            },
            {
                'description': 'Train pass ticket for monthly commute',
                'amount': Decimal('75.00'),
                'category': 'Travel',
                'date': today - datetime.timedelta(days=65),
                'notes': 'Metro pass'
            },
            {
                'description': 'Books on Algorithms and Data Structures',
                'amount': Decimal('49.50'),
                'category': 'Education',
                'date': today - datetime.timedelta(days=95),
                'notes': 'College reference textbook'
            },
            {
                'description': 'PlayStation online game purchase',
                'amount': Decimal('39.99'),
                'category': 'Entertainment',
                'date': today - datetime.timedelta(days=125),
                'notes': 'Weekend leisure'
            },
        ]

        count = 0
        for item in sample_expenses:
            obj, created_exp = Expense.objects.get_or_create(
                user=demo_user,
                description=item['description'],
                date=item['date'],
                defaults={
                    'amount': item['amount'],
                    'category': item['category'],
                    'notes': item['notes']
                }
            )
            if created_exp:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} sample expenses for demo user.'))

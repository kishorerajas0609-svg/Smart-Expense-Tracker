from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Expense(models.Model):
    CATEGORY_FOOD = 'Food'
    CATEGORY_TRAVEL = 'Travel'
    CATEGORY_BILLS = 'Bills'
    CATEGORY_ENTERTAINMENT = 'Entertainment'
    CATEGORY_HEALTHCARE = 'Healthcare'
    CATEGORY_EDUCATION = 'Education'
    CATEGORY_SHOPPING = 'Shopping'
    CATEGORY_OTHER = 'Other'

    CATEGORY_CHOICES = [
        (CATEGORY_FOOD, 'Food & Dining'),
        (CATEGORY_TRAVEL, 'Travel & Transport'),
        (CATEGORY_BILLS, 'Bills & Utilities'),
        (CATEGORY_ENTERTAINMENT, 'Entertainment & Leisure'),
        (CATEGORY_HEALTHCARE, 'Healthcare & Medical'),
        (CATEGORY_EDUCATION, 'Education & Learning'),
        (CATEGORY_SHOPPING, 'Shopping & Groceries'),
        (CATEGORY_OTHER, 'Other / Miscellaneous'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    description = models.CharField(
        max_length=255,
        help_text="Brief description of the expense"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'), message="Amount must be greater than zero.")],
        help_text="Amount spent (greater than zero)"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_OTHER,
        help_text="Spending category"
    )
    date = models.DateField(
        default=timezone.now,
        help_text="Date when expense was incurred"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes or details"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.description} - ₹{self.amount:.2f} ({self.category})"

    @property
    def category_badge_class(self):
        badge_map = {
            self.CATEGORY_FOOD: 'badge-food',
            self.CATEGORY_TRAVEL: 'badge-travel',
            self.CATEGORY_BILLS: 'badge-bills',
            self.CATEGORY_ENTERTAINMENT: 'badge-entertainment',
            self.CATEGORY_HEALTHCARE: 'badge-healthcare',
            self.CATEGORY_EDUCATION: 'badge-education',
            self.CATEGORY_SHOPPING: 'badge-shopping',
            self.CATEGORY_OTHER: 'badge-other',
        }
        return badge_map.get(self.category, 'badge-other')

    @property
    def category_icon(self):
        icon_map = {
            self.CATEGORY_FOOD: 'bi-cup-hot-fill',
            self.CATEGORY_TRAVEL: 'bi-car-front-fill',
            self.CATEGORY_BILLS: 'bi-receipt-cutoff',
            self.CATEGORY_ENTERTAINMENT: 'bi-controller',
            self.CATEGORY_HEALTHCARE: 'bi-heart-pulse-fill',
            self.CATEGORY_EDUCATION: 'bi-book-half',
            self.CATEGORY_SHOPPING: 'bi-bag-heart-fill',
            self.CATEGORY_OTHER: 'bi-tags-fill',
        }
        return icon_map.get(self.category, 'bi-tags-fill')

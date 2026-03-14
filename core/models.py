from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    )
    
    INCOME_CATEGORIES = [
        (1, ' Salary'),
        (2, ' Business'),
        (3, ' Investment'),
        (4, ' Rent'),
        (5, ' Gift'),
        (6, ' Freelance'),
        (7, ' Bonus'),
        (8, ' Refund'),
        (9, ' Dividend'),
        (10, ' Prize'),
        (11, ' Consulting'),
        (12, ' Allowance'),
        (13, ' Commission'),
        (14, ' Interest'),
        (15, ' Other Income'),
    ]
    
    EXPENSE_CATEGORIES = [
        (16, ' Food & Dining'),
        (17, ' Transportation'),
        (18, ' Rent/Utilities'),
        (19, ' Shopping'),
        (20, ' Entertainment'),
        (21, ' Healthcare'),
        (22, ' Education'),
        (23, ' Travel'),
        (24, ' Fitness'),
        (25, ' Pets'),
        (26, ' Insurance'),
        (27, ' Mobile/Internet'),
        (28, ' Personal Care'),
        (29, ' Gifts'),
        (30, ' Other Expenses'),
    ]
    
    CATEGORY_CHOICES = INCOME_CATEGORIES + EXPENSE_CATEGORIES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    date = models.DateField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.IntegerField(choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.description} - Rs.{self.amount}"
    
    def get_category_display(self):
        for cat_id, cat_name in self.CATEGORY_CHOICES:
            if cat_id == self.category:
                return cat_name
        return "Unknown"


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['deadline']
    
    def __str__(self):
        return self.name
    
    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    def is_completed(self):
        return self.current_amount >= self.target_amount
    
    def remaining_days(self):
        if self.deadline > date.today():
            return (self.deadline - date.today()).days
        return 0


class Budget(models.Model):
    PERIOD_CHOICES = (
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.IntegerField(choices=Transaction.CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.get_category_display()} - Rs.{self.amount}"
    
    def get_category_display(self):
        for cat_id, cat_name in Transaction.CATEGORY_CHOICES:
            if cat_id == self.category:
                return cat_name
        return "Unknown"
    
    def spent_amount(self):
        from django.db.models import Sum
        if self.period == 'MONTHLY':
            transactions = Transaction.objects.filter(
                user=self.user,
                category=self.category,
                type='EXPENSE',
                date__year=self.start_date.year,
                date__month=self.start_date.month
            )
        elif self.period == 'YEARLY':
            transactions = Transaction.objects.filter(
                user=self.user,
                category=self.category,
                type='EXPENSE',
                date__year=self.start_date.year
            )
        else:
            quarter = (self.start_date.month - 1) // 3 + 1
            months = [(quarter-1)*3 + 1, (quarter-1)*3 + 2, (quarter-1)*3 + 3]
            transactions = Transaction.objects.filter(
                user=self.user,
                category=self.category,
                type='EXPENSE',
                date__year=self.start_date.year,
                date__month__in=months
            )
        
        total = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        return total
    
    def remaining_amount(self):
        return self.amount - self.spent_amount()
    
    def utilization_percentage(self):
        if self.amount > 0:
            return (self.spent_amount() / self.amount) * 100
        return 0
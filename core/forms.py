from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Transaction, Goal, Budget
from datetime import date

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username.replace(' ', '').isalnum():
            raise forms.ValidationError("Username can only contain letters and numbers")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'description', 'date', 'type', 'category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'type': forms.HiddenInput(),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '200'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Type अनुसार category filter गर्ने
        trans_type = None
        if self.data.get('type'):
            trans_type = self.data.get('type')
        elif self.instance and self.instance.pk:
            trans_type = self.instance.type
        elif self.initial.get('type'):
            trans_type = self.initial.get('type')
        
        if trans_type == 'INCOME':
            self.fields['category'].choices = Transaction.INCOME_CATEGORIES
        elif trans_type == 'EXPENSE':
            self.fields['category'].choices = Transaction.EXPENSE_CATEGORIES
        else:
            self.fields['category'].choices = [('', '-- Select Type First --')] + Transaction.INCOME_CATEGORIES + Transaction.EXPENSE_CATEGORIES
        
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        return amount
    
    def clean_date(self):
        date_value = self.cleaned_data.get('date')
        if date_value > date.today():
            raise forms.ValidationError("Future dates are not allowed")
        return date_value


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'current_amount', 'deadline', 'description']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'current_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_target_amount(self):
        amount = self.cleaned_data.get('target_amount')
        if amount <= 0:
            raise forms.ValidationError("Target amount must be greater than 0")
        return amount
    
    def clean_current_amount(self):
        amount = self.cleaned_data.get('current_amount', 0)
        target = self.cleaned_data.get('target_amount', 0)
        if amount > target:
            raise forms.ValidationError("Current amount cannot exceed target amount")
        return amount
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline < date.today():
            raise forms.ValidationError("Deadline must be a future date")
        return deadline


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'period', 'start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = Transaction.INCOME_CATEGORIES + Transaction.EXPENSE_CATEGORIES
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Budget amount must be greater than 0")
        return amount


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})
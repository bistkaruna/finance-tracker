from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from .models import Transaction, Goal, Budget
from .forms import (
    CustomUserCreationForm, TransactionForm, GoalForm, 
    BudgetForm, CustomPasswordChangeForm
)


def home(request):
    """Home page view"""
    return render(request, 'core/home.html')




def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'core/login.html')


def logout_view(request):
    """User logout view"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('home')
    return render(request, 'core/logout.html')




@login_required
def dashboard(request):
    """Dashboard view showing financial overview"""
    today_date = date.today()
    
    # Monthly stats
    monthly_income = Transaction.objects.filter(
        user=request.user,
        type='INCOME',
        date__year=today_date.year,
        date__month=today_date.month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_expense = Transaction.objects.filter(
        user=request.user,
        type='EXPENSE',
        date__year=today_date.year,
        date__month=today_date.month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_balance = monthly_income - monthly_expense
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-date')[:5]
    
    # Active goals
    all_goals = Goal.objects.filter(user=request.user)
    active_goals = []
    for goal in all_goals:
        if goal.deadline >= today_date and not goal.is_completed():
            active_goals.append(goal)
    active_goals = sorted(active_goals, key=lambda g: g.deadline)[:3]
    
    context = {
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_balance': monthly_balance,
        'recent_transactions': recent_transactions,
        'active_goals': active_goals,
        'today': today_date,
    }
    return render(request, 'core/dashboard.html', context)



@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'core/profile.html', {'user': request.user})


@login_required
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'core/change_password.html', {'form': form})




@login_required
def transaction_list(request):
    """List all transactions with filters"""
    transactions = Transaction.objects.filter(user=request.user)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter in ['INCOME', 'EXPENSE']:
        transactions = transactions.filter(type=type_filter)
    
    # Date filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    # Totals
    total_income = transactions.filter(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expense
    
    # Pagination
    paginator = Paginator(transactions.order_by('-date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'search_query': search_query,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'core/transaction_list.html', context)


@login_required
def transaction_create(request):
    """Create a new transaction"""
    transaction_type = request.GET.get('type', '')
    
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, f'{transaction.get_type_display()} added successfully!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        if transaction_type in ['INCOME', 'EXPENSE']:
            initial['type'] = transaction_type
        form = TransactionForm(initial=initial)
    
    if transaction_type == 'INCOME':
        title = 'Add New Income'
    elif transaction_type == 'EXPENSE':
        title = 'Add New Expense'
    else:
        title = 'Add Transaction'
    
    return render(request, 'core/transaction_form.html', {
        'form': form,
        'title': title,
        'transaction_type': transaction_type,
        'today': date.today()
    })


@login_required
def transaction_detail(request, pk):
    """View transaction details"""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    return render(request, 'core/transaction_detail.html', {'transaction': transaction})


@login_required
def transaction_update(request, pk):
    """Update a transaction"""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transaction_detail', pk=transaction.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TransactionForm(instance=transaction)
    
    title = f'Edit {transaction.get_type_display()}'
    return render(request, 'core/transaction_form.html', {
        'form': form,
        'title': title,
        'transaction_type': transaction.type,
        'today': date.today()
    })


@login_required
def transaction_delete(request, pk):
    """Delete a transaction"""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transaction_list')
    
    return render(request, 'core/transaction_confirm_delete.html', {'transaction': transaction})




@login_required
def goal_list(request):
    """List all goals"""
    goals = Goal.objects.filter(user=request.user)
    today_date = date.today()
    
    # Filter by status
    status = request.GET.get('status', '')
    
    if status == 'active':
        goals = [g for g in goals if g.deadline >= today_date and not g.is_completed()]
    elif status == 'completed':
        goals = [g for g in goals if g.is_completed()]
    elif status == 'overdue':
        goals = [g for g in goals if g.deadline < today_date and not g.is_completed()]
    
    context = {
        'goals': goals,
        'today': today_date,
        'status': status,
    }
    return render(request, 'core/goal_list.html', context)


@login_required
def goal_create(request):
    """Create a new goal"""
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal created successfully!')
            return redirect('goal_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GoalForm()
    
    return render(request, 'core/goal_form.html', {
        'form': form,
        'title': 'Create New Goal',
        'today': date.today()
    })


@login_required
def goal_detail(request, pk):
    """View goal details"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    return render(request, 'core/goal_detail.html', {'goal': goal, 'today': date.today()})


@login_required
def goal_update(request, pk):
    """Update a goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goal updated successfully!')
            return redirect('goal_detail', pk=goal.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GoalForm(instance=goal)
    
    return render(request, 'core/goal_form.html', {
        'form': form,
        'title': f'Edit {goal.name}',
        'today': date.today()
    })


@login_required
def goal_delete(request, pk):
    """Delete a goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully!')
        return redirect('goal_list')
    
    return render(request, 'core/goal_confirm_delete.html', {'goal': goal, 'today': date.today()})




@login_required
def budget_list(request):
    """List all budgets"""
    budgets = Budget.objects.filter(user=request.user)
    today_date = date.today()
    
    # Calculate spent amounts
    for budget in budgets:
        budget.spent = budget.spent_amount()
        budget.remaining = budget.remaining_amount()
        budget.utilization = budget.utilization_percentage()
    
    return render(request, 'core/budget_list.html', {
        'budgets': budgets,
        'today': today_date
    })


@login_required
def budget_create(request):
    """Create a new budget"""
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget created successfully!')
            return redirect('budget_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BudgetForm()
    
    
    categories = Transaction.INCOME_CATEGORIES + Transaction.EXPENSE_CATEGORIES
    
    return render(request, 'core/budget_form.html', {
        'form': form,
        'title': 'Create New Budget',
        'categories': categories,
    })


@login_required
def budget_update(request, pk):
    """Update a budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated successfully!')
            return redirect('budget_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BudgetForm(instance=budget)
    
  
    categories = Transaction.INCOME_CATEGORIES + Transaction.EXPENSE_CATEGORIES
    
    return render(request, 'core/budget_form.html', {
        'form': form,
        'title': 'Edit Budget',
        'categories': categories,
    })


@login_required
def budget_delete(request, pk):
    """Delete a budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('budget_list')
    
    return render(request, 'core/budget_confirm_delete.html', {'budget': budget})



@login_required
def financial_report(request):
    """Generate financial reports"""
    today_date = date.today()
    
    # Monthly summary
    monthly_income = Transaction.objects.filter(
        user=request.user,
        type='INCOME',
        date__year=today_date.year,
        date__month=today_date.month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_expense = Transaction.objects.filter(
        user=request.user,
        type='EXPENSE',
        date__year=today_date.year,
        date__month=today_date.month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_summary = {
        'income': monthly_income,
        'expense': monthly_expense,
        'balance': monthly_income - monthly_expense,
    }
    
    # Category breakdown
    category_data = []
    transactions = Transaction.objects.filter(user=request.user)
    
    # Income categories
    for cat_id, cat_name in Transaction.INCOME_CATEGORIES:
        total = transactions.filter(type='INCOME', category=cat_id).aggregate(Sum('amount'))['amount__sum'] or 0
        count = transactions.filter(type='INCOME', category=cat_id).count()
        if total > 0 or count > 0:
            category_data.append({
                'name': cat_name,
                'type': 'Income',
                'amount': total,
                'count': count
            })
    
    # Expense categories
    for cat_id, cat_name in Transaction.EXPENSE_CATEGORIES:
        total = transactions.filter(type='EXPENSE', category=cat_id).aggregate(Sum('amount'))['amount__sum'] or 0
        count = transactions.filter(type='EXPENSE', category=cat_id).count()
        if total > 0 or count > 0:
            category_data.append({
                'name': cat_name,
                'type': 'Expense',
                'amount': total,
                'count': count
            })
    
    # Monthly trends (last 6 months)
    months_data = []
    for i in range(5, -1, -1):
        month_date = today_date - timedelta(days=30*i)
        year = month_date.year
        month = month_date.month
        
        income = transactions.filter(
            type='INCOME',
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        expense = transactions.filter(
            type='EXPENSE',
            date__year=year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        months_data.append({
            'month': month_date.strftime('%B %Y'),
            'income': income,
            'expense': expense,
            'balance': income - expense
        })
    
    context = {
        'monthly_summary': monthly_summary,
        'category_data': category_data,
        'months_data': months_data,
        'today': today_date,
    }
    return render(request, 'core/financial_report.html', context)
import json
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse

from .models import Expense
from .forms import ExpenseForm, UserRegisterForm, UserProfileForm
from .utils import (
    CATEGORY_KEYWORDS, predict_category,
    generate_expense_csv, generate_expense_pdf
)


def get_filtered_expenses(request):
    """Filter user expenses based on search, time filter, category, and sorting."""
    expenses = Expense.objects.filter(user=request.user)
    today = timezone.localdate()

    q = request.GET.get('q', '').strip()
    if q:
        expenses = expenses.filter(Q(description__icontains=q) | Q(notes__icontains=q))

    time_filter = request.GET.get('time_filter', 'all')
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    filter_label = "All Time"

    if time_filter == 'today':
        expenses = expenses.filter(date=today)
        filter_label = f"Today ({today.strftime('%b %d, %Y')})"
    elif time_filter == 'this_week':
        week_start = today - timedelta(days=today.weekday())
        expenses = expenses.filter(date__gte=week_start, date__lte=today)
        filter_label = f"This Week ({week_start.strftime('%b %d')} - {today.strftime('%b %d, %Y')})"
    elif time_filter == 'this_month':
        month_start = today.replace(day=1)
        expenses = expenses.filter(date__gte=month_start, date__lte=today)
        filter_label = f"This Month ({month_start.strftime('%b %Y')})"
    elif time_filter == 'custom' or (start_date and end_date):
        if start_date:
            try:
                expenses = expenses.filter(date__gte=start_date)
            except ValueError:
                pass
        if end_date:
            try:
                expenses = expenses.filter(date__lte=end_date)
            except ValueError:
                pass
        filter_label = f"Custom: {start_date or 'Any'} to {end_date or 'Any'}"

    category = request.GET.get('category', '').strip()
    if category and category != 'all':
        expenses = expenses.filter(category=category)
        filter_label += f" | Category: {category}"

    sort = request.GET.get('sort', '-date')
    valid_sorts = ['-date', 'date', '-amount', 'amount']
    if sort in valid_sorts:
        expenses = expenses.order_by(sort, '-id')
    else:
        expenses = expenses.order_by('-date', '-id')

    return expenses, filter_label

def register_view(request):
    """User registration page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            login(request, user)
            messages.success(request, f"Welcome to Smart Expense Tracker, {username}! Your account has been created.")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please check the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'expenses/register.html', {'form': form})


def login_view(request):
    """User login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'expenses/login.html', {'form': form})


def logout_view(request):
    """User logout."""
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        messages.info(request, "You have been logged out successfully. See you soon!")
        return redirect('login')


@login_required
def dashboard_view(request):
    """Modern dashboard summarizing spending, recent transactions, and charts."""
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    user_expenses = Expense.objects.filter(user=request.user)

    today_total = user_expenses.filter(date=today).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    week_total = user_expenses.filter(date__gte=week_start, date__lte=today).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    month_total = user_expenses.filter(date__gte=month_start, date__lte=today).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_transactions = user_expenses.count()
    all_time_total = user_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    recent_expenses = user_expenses.order_by('-date', '-created_at')[:6]

    category_summary = (
        user_expenses.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    category_labels = []
    category_data = []
    category_colors = {
        'Food': '#F59E0B',         
        'Travel': '#06B6D4',         
        'Bills': '#EF4444',          
        'Entertainment': '#8B5CF6',  
        'Healthcare': '#10B981',     
        'Education': '#3B82F6',      
        'Shopping': '#EC4899',       
        'Other': '#64748B',          
    }
    chart_bg_colors = []

    for item in category_summary:
        category_labels.append(item['category'])
        category_data.append(float(item['total']))
        chart_bg_colors.append(category_colors.get(item['category'], '#94A3B8'))

    monthly_labels = []
    monthly_data = []
    
    current_year = today.year
    current_month = today.month

    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        
        m_start = today.replace(year=y, month=m, day=1)
        if m == 12:
            m_end = today.replace(year=y + 1, month=1, day=1) - timedelta(days=1)
        else:
            m_end = today.replace(year=y, month=m + 1, day=1) - timedelta(days=1)

        m_sum = user_expenses.filter(date__gte=m_start, date__lte=m_end).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        monthly_labels.append(m_start.strftime("%b %Y"))
        monthly_data.append(float(m_sum))

    context = {
        'today_total': today_total,
        'week_total': week_total,
        'month_total': month_total,
        'total_transactions': total_transactions,
        'all_time_total': all_time_total,
        'recent_expenses': recent_expenses,
        'category_summary': category_summary,
        'category_labels_json': json.dumps(category_labels),
        'category_data_json': json.dumps(category_data),
        'category_colors_json': json.dumps(chart_bg_colors),
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_data_json': json.dumps(monthly_data),
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def add_expense_view(request):
    """Add a new expense with smart keyword suggestion."""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, f'Expense "{expense.description}" of ${expense.amount:.2f} was added successfully!')
            return redirect('expense_list')
        else:
            messages.error(request, "Failed to save expense. Please correct the highlighted errors.")
    else:
        
        form = ExpenseForm(initial={'date': timezone.localdate()})

    context = {
        'form': form,
        'category_keywords_json': json.dumps(CATEGORY_KEYWORDS),
        'categories': Expense.CATEGORY_CHOICES,
    }
    return render(request, 'expenses/add_expense.html', context)


@login_required
def expense_list_view(request):
    """Searchable, filterable, sortable, paginated expense list."""
    expenses, filter_label = get_filtered_expenses(request)

    filtered_total = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    filtered_count = expenses.count()

    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    query_string = get_params.urlencode()

    context = {
        'page_obj': page_obj,
        'filtered_total': filtered_total,
        'filtered_count': filtered_count,
        'filter_label': filter_label,
        'query_string': query_string,
        'categories': Expense.CATEGORY_CHOICES,
        'current_q': request.GET.get('q', ''),
        'current_time_filter': request.GET.get('time_filter', 'all'),
        'current_start_date': request.GET.get('start_date', ''),
        'current_end_date': request.GET.get('end_date', ''),
        'current_category': request.GET.get('category', 'all'),
        'current_sort': request.GET.get('sort', '-date'),
    }
    return render(request, 'expenses/expense_list.html', context)

@login_required
def edit_expense_view(request, pk):
    """Edit an existing expense belonging strictly to the logged-in user."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f'Expense "{expense.description}" was updated successfully!')
            return redirect('expense_list')
        else:
            messages.error(request, "Failed to update expense. Please check the errors.")
    else:
        form = ExpenseForm(instance=expense)

    context = {
        'form': form,
        'expense': expense,
        'category_keywords_json': json.dumps(CATEGORY_KEYWORDS),
    }
    return render(request, 'expenses/edit_expense.html', context)


@login_required
def delete_expense_view(request, pk):
    """Delete an expense record with confirmation."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        desc = expense.description
        amt = expense.amount
        expense.delete()
        messages.success(request, f'Expense "{desc}" (${amt:.2f}) was permanently deleted.')
        return redirect('expense_list')

    return render(request, 'expenses/delete_expense.html', {'expense': expense})


@login_required
def reports_view(request):
    """Dedicated Reports and Analytics page with filterable downloads."""
    expenses, filter_label = get_filtered_expenses(request)

    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_count = expenses.count()
    avg_spent = (total_spent / total_count) if total_count > 0 else Decimal('0.00')

    category_summary = (
        expenses.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    breakdown_list = []
    for item in category_summary:
        pct = (item['total'] / total_spent * 100) if total_spent > 0 else 0
        breakdown_list.append({
            'category': item['category'],
            'total': item['total'],
            'count': item['count'],
            'percentage': round(pct, 1),
        })

    query_string = request.GET.urlencode()

    context = {
        'expenses': expenses[:50],  
        'total_spent': total_spent,
        'total_count': total_count,
        'avg_spent': avg_spent,
        'breakdown_list': breakdown_list,
        'filter_label': filter_label,
        'query_string': query_string,
        'categories': Expense.CATEGORY_CHOICES,
        'current_time_filter': request.GET.get('time_filter', 'all'),
        'current_start_date': request.GET.get('start_date', ''),
        'current_end_date': request.GET.get('end_date', ''),
        'current_category': request.GET.get('category', 'all'),
        'current_q': request.GET.get('q', ''),
    }
    return render(request, 'expenses/reports.html', context)


@login_required
def export_csv_view(request):
    """Export filtered user expenses to CSV file."""
    expenses, filter_label = get_filtered_expenses(request)
    return generate_expense_csv(request.user, expenses, filter_info=filter_label)


@login_required
def export_pdf_view(request):
    """Export filtered user expenses to professional PDF document."""
    expenses, filter_label = get_filtered_expenses(request)
    return generate_expense_pdf(request.user, expenses, filter_info=filter_label)

@login_required
def profile_view(request):
    """Account overview and settings (update info & password)."""
    user_expenses = Expense.objects.filter(user=request.user)
    total_spent = user_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_count = user_expenses.count()

    profile_form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile information has been updated successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Failed to update profile. Please check the inputs.")
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Failed to change password. Please check requirements.")

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'total_spent': total_spent,
        'total_count': total_count,
    }
    return render(request, 'expenses/profile.html', context)

@login_required
def predict_category_api(request):
    """Predict category from keyword in text query parameter."""
    text = request.GET.get('text', '')
    predicted = predict_category(text)
    return JsonResponse({'category': predicted})

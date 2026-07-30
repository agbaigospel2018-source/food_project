from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from orders.models import Order
from menu.models import MenuItemReview
from .forms import RegisterForm, ProfileUpdateForm
# Create your views here.

def redirect_vendor(user, destination='vendors:vendor_dashboard'):
    if hasattr(user, 'vendor_profile'):
        return redirect(destination)
    return redirect('vendors:create_vendor')

def redirect_authenticated_user(user):
    if user.role == 'vendor':
        return redirect_vendor(user)
    return redirect('profile')

# -----------Register View
def register_view(request):
    if request.user.is_authenticated:
        return redirect_authenticated_user(request.user)
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            if user.role == 'vendor':
                request.session['pending_vendor_user_id'] = user.id
                messages.info(
                    request,
                    'Account created. Please complete your business profile to finish logging in.'
                )
                return redirect('vendors:create_vendor')

            login(request, user)
            
            messages.success(
                request,
                'Account created successfully.'
            )
            return redirect('profile')
    else:
        form =RegisterForm()
    
    context = {
        'form' : form
    }
    
    return render(
        request, 'accounts/register.html', context 
    )
    
# -----------Login View
def login_view(request):

    if request.user.is_authenticated:
        return redirect_authenticated_user(request.user)

    if request.method == 'POST':

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            if user.role == 'vendor' and not hasattr(user, 'vendor_profile'):
                request.session['pending_vendor_user_id'] = user.id
                messages.info(
                    request,
                    'Please complete your business profile to finish logging in.'
                )
                return redirect('vendors:create_vendor')

            login(request, user)

            messages.success(
                request,
                'Logged in successfully.'
            )

            if user.role == 'vendor':
                return redirect('vendors:vendor_dashboard')
            return redirect('home')
        else:
            messages.error(
                request,
                "Invalid username or password"
            )

    else:
        form = AuthenticationForm()
            
      

    context = {
        'form': form
    }

    return render(
        request,
        'accounts/login.html',
        context
    )
    
# -----------Logout View
@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        'Logged out successfully.'
    )

    return redirect('home')

# -----------Profile View
@login_required
def profile_view(request):
    if request.user.role == 'vendor':
        return redirect_vendor(request.user, destination='vendors:vendor_profile')

    total_orders = Order.objects.filter(student=request.user).count()
    total_reviews = MenuItemReview.objects.filter(student=request.user, is_approved=True).count()
    recent_orders = Order.objects.filter(student=request.user).order_by('-created_at')[:5]

    context = {
        'user': request.user,
        'total_orders': total_orders,
        'total_reviews': total_reviews,
        'recent_orders': recent_orders,
    }

    return render(
        request,
        'accounts/profile.html',
        context
    )
    
# -----------Edit Profile View
@login_required
def edit_profile_view(request):

    if request.method == 'POST':

        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Profile updated successfully.'
            )

            return redirect('profile')

    else:

        form = ProfileUpdateForm(
            instance=request.user
        )

    context = {
        'form': form
    }

    return render(
        request,
        'accounts/edit_profile.html',
        context
    )
    
# -----------Change Password View
@login_required
def change_password_view(request):

    if request.method == 'POST':

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                'Password changed successfully.'
            )

            return redirect('profile')

    else:

        form = PasswordChangeForm(
            request.user
        )

    context = {
        'form': form
    }

    return render(
        request,
        'accounts/change_password.html',
        context
    )
    

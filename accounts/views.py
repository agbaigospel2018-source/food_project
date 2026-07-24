from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .forms import RegisterForm, ProfileUpdateForm
# Create your views here.

# -----------Register View
def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
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
        return redirect('profile')

    if request.method == 'POST':

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                'Logged in successfully.'
            )

            return redirect('profile')
        else:
            messages.success(
                request,
                "Account does't exist. Create new account to login"
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

    return redirect('login')

# -----------Profile View
@login_required
def profile_view(request):

    context = {
        'user': request.user
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
    

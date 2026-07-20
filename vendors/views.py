from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import VendorForm
from django.shortcuts import get_object_or_404

# -----------Vendor Dashboard View
@login_required
def vendor_dashboard(request):

    context = {}

    return render(
        request,
        'vendors/dashboard.html',
        context
    )
    
# -----------Vendor Profile View
@login_required
def vendor_profile(request):

    vendor = request.user.vendor_profile

    context = {
        'vendor': vendor
    }

    return render(
        request,
        'vendors/profile.html',
        context
    )
    
# ------------create vendor view
@login_required
def create_vendor(request):

    if request.method == 'POST':

        form = VendorForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            vendor = form.save(
                commit=False
            )

            vendor.owner = request.user

            vendor.save()

            messages.success(
                request,
                'Vendor profile created.'
            )

            return redirect(
                'vendor_profile'
            )

    else:

        form = VendorForm()

    context = {
        'form': form
    }

    return render(
        request,
        'vendors/create_vendor.html',
        context
    )
    
# ------------edit vendor view
@login_required
def edit_vendor(request):

    vendor = request.user.vendor_profile

    if request.method == 'POST':

        form = VendorForm(
            request.POST,
            request.FILES,
            instance=vendor
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Profile updated.'
            )

            return redirect(
                'vendor_profile'
            )

    else:

        form = VendorForm(
            instance=vendor
        )

    context = {
        'form': form
    }

    return render(
        request,
        'vendors/edit_vendor.html',
        context
    )
    
# ------------toggle vendor status view
@login_required
def toggle_vendor_status(request):

    vendor = get_object_or_404(
        request.user.vendor_profile.__class__,
        owner=request.user
    )

    vendor.is_open = not vendor.is_open

    vendor.save()

    return redirect(
        'vendor_profile'
    )
from django.shortcuts import  render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Vendor
from .forms import VendorForm
from orders.models import Order

# Create your views here.

# Student views
from django.db.models import Q

def vendor_list(request):

    vendors = Vendor.objects.all().order_by("business_name")

    query = request.GET.get("q")

    status = request.GET.get("status")

    if query:
        vendors = vendors.filter(
            Q(business_name__icontains=query) |
            Q(location__icontains=query)
        )

    if status == "open":
        vendors = vendors.filter(is_open=True)

    elif status == "closed":
        vendors = vendors.filter(is_open=False)

    context = {
        "vendors": vendors,
        "total_vendors": Vendor.objects.count(),
        "open_vendors": Vendor.objects.filter(is_open=True).count(),
        "page_title": "Discover Amazing Restaurants",
        "page_subtitle": "Order from your favorite campus restaurants and skip the queue.",
    }

    return render(
        request,
        "vendors/vendor_list.html",
        context
    )

def vendor_detail(request, pk):
    
    """
    Display a single vendor.
    """
    
    vendor = get_object_or_404(Vendor, pk=pk)
    
    context = {
        'vendor': vendor
    }
    
    return render(request, 'vendors/vendor_detail.html', context)


# Vendor views
@login_required
def vendor_dashboard(request):
    
    """
    Vendor dashboard.   
    """
    
    vendor = get_object_or_404(Vendor, owner=request.user)
    
    context = {
        'vendor': vendor,
        
        # Placehoder statistics
        'total_orders': 0,
        'pending_orders': 0,
        'completed_orders': 0,
        'cancelled_orders': 0,
        'total_menu_items': 0,
        'today_revenue': 0,
    }
    
    return render(request, 'vendors/vendor_dashboard.html', context)


@login_required
def vendor_profile(request):
    
    """Vendor Profile
    """
    
    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )
    
    context = {
        'vendor': vendor
    }
    
    return render(request, 'vendors/vendor_profile.html', context)


@login_required
def create_vendor(request):
    
    """Create vendor profile
    """
    
    if Vendor.objects.filter(owner=request.user).exists():
        
        messages.warning(
            request,
            'You already have a vendor profile.'
        )
        
        return redirect('vendor_profile')

    if request.method == 'POST':
        
        form = VendorForm(
            request.POST,
            request.FILES
        )
        
        if form.is_valid():
            
            vendor = form.save(commit=False)

            vendor.owner = request.user
            
            vendor.save()

            messages.success(
                request,
                'Your vendor profile has been created.'
            )
            
            return redirect('vendor_dashboard')

    else: 
        form = VendorForm()
        
    context = {
        'form': form
    }
    
    return render(request, 'vendors/create_vendor.html', context)

@login_required
def edit_vendor(request):
    
    """Update vendor profile
    """
    
    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )
    
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
                'Your vendor profile has been updated.'
            )
            
            return redirect('vendor_profile')

            
    else:
        form = VendorForm(instance=vendor)
        
    context = {
        'form': form,
        'vendor': vendor
    }
    
    return render(request, 'vendors/edit_vendor.html', context)
    
    
@login_required
def toggle_vendor_status(request):
    """
    Open/Close vendor.
    """

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    vendor.is_open = not vendor.is_open

    vendor.save(update_fields=["is_open"])

    if vendor.is_open:

        messages.success(
            request,
            "Your restaurant is now Open."
        )

    else:

        messages.success(
            request,
            "Your restaurant is now Closed."
        )

    return redirect(
        "vendor_profile"
    )


@login_required
def delete_vendor(request):
    """
    Delete vendor profile.
    """

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    if request.method == "POST":

        vendor.delete()

        messages.success(
            request,
            "Vendor profile deleted successfully."
        )

        return redirect("home")

    context = {
        "vendor": vendor
    }

    return render(
        request,
        "vendors/delete_vendor.html",
        context
    )
    
    
@login_required
def vendor_orders(request):
    """
    Display all orders belonging to the logged-in vendor.
    """

    vendor = get_object_or_404(
        Vendor,
        owner=request.user
    )

    orders = (
        Order.objects
        .filter(vendor=vendor)
        .select_related("student")
        .order_by("-created_at")
    )

    status = request.GET.get("status")

    if status:
        orders = orders.filter(status=status)

    context = {
        "vendor": vendor,
        "orders": orders,
        "selected_status": status,
    }

    return render(
        request,
        "vendors/vendor_orders.html",
        context
    )
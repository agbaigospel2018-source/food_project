from django.shortcuts import  render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Vendor
from .forms import VendorForm

# Create your views here.

# Student views
def vendor_list(request):
    
    """ 
    Display all vendors.
    """
    
    
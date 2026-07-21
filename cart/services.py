from django.db import transaction

from .models import Cart, CartItem
from menu.models import MenuItem

from django.core.exceptions import ValidationError

def get_or_create_cart(student):
    
    """ 
    Get the student's active cart or create one.
    """
    
    cart, created = Cart.objects.get_or_create(
        student=student,
    )
    
    return cart

def get_cart(student):
    
    """ 
    Return the student's cart
    """
    
    return (
        Cart.objects
        .prefetch_related('items__menu_item')
        .get(student=student)
    )
    
    
@transaction.atomic
def add_to_cart(student, menu_item, quantity=1):
    """
    Add a menu item to the student's cart.
    """

    cart = get_or_create_cart(student)

    existing_item = cart.items.select_related(
        "menu_item__vendor"
    ).first()

    if existing_item and existing_item.menu_item.vendor != menu_item.vendor:
        raise ValidationError(
            "Your cart contains items from another vendor. "
            "Please clear your cart before ordering from a different vendor."
        )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=menu_item,
        defaults={
            "quantity": quantity,
        },
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=["quantity"])

    return cart_item
    
def remove_from_cart(student, menu_item):
    
    """
    Remove a cart item from the student's cart.
    """
    
    cart = get_or_create_cart(student)
    
    CartItem.objects.filter(
        cart=cart,
        menu_item=menu_item,
    ).delete()
    
    
def update_cart_item_quantity(cart_item, quantity):
    
    """ 
    Update the quantity of a cart item.
    """
    
    if quantity <= 0:
        cart_item.delete()
        return
    
    cart_item.quantity = quantity
    cart_item.save(update_fields=['quantity'])

    
def clear_cart(student):
    
    """ 
    Remove all items from the student's cart.
    """
    
    cart = get_or_create_cart(student)
    
    cart.items.all().delete()
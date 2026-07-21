from django.db import transaction

from .models import Order, OrderItem, OrderStatus


def update_order_status(order, status):
    
    """
    Update the satus of an order.
    """
    
    order.status = status
    order.save(update_fields=['status'])

    return order


def cancel_order(order):
    
    """
    Cancel an order.
    """
    
    return update_order_status(
        order,
        OrderStatus.CANCELLED
    )
    
    
def complete_order(order):
    
    """
    Mark an order as completed.
    """
    
    return update_order_status(
        order,
        OrderStatus.COMPLETED
    )
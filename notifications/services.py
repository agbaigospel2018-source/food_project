from .models import Notification, NotificationType
def notify_user(recipient, notification_type, title, message, order=None):
    """Create and return a notification for a single user."""
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        order=order,
    )
def notify_order_placed(order):
    """Notify the vendor that a new order has been placed."""
    notify_user(
        recipient=order.vendor.owner,
        notification_type=NotificationType.NEW_ORDER,
        title='New Order Received!',
        message=f'Order #{order.short_id()} has been placed by {order.student.username}. Total: ₦{order.total_amount}',
        order=order,
    )
def notify_order_status_changed(order):
    """Notify the student when their order status changes."""
    status_messages = {
        'accepted': ('Order Accepted', 'Your order has been accepted and will be prepared shortly.'),
        'preparing': ('Order Being Prepared', 'Your order is now being prepared.'),
        'ready': ('Order Ready!', 'Your order is ready for pickup!'),
        'completed': ('Order Completed', 'Your order has been completed. Enjoy your meal!'),
        'cancelled': ('Order Cancelled', 'Your order has been cancelled.'),
        'rejected': ('Order Rejected', 'Unfortunately, your order has been rejected by the vendor.'),
    }
    if order.status in status_messages:
        title, message = status_messages[order.status]
        notify_user(
            recipient=order.student,
            notification_type=NotificationType(f'order_{order.status}'),
            title=title,
            message=f'{message} (Order #{order.short_id()})',
            order=order,
        )
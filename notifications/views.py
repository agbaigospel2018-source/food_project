from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Notification

@login_required
def notifications_page(request):
    """Render the notifications frontend page."""
    return render(request, 'notifications/notifications_page.html')


@login_required
def notification_list(request):
    """Return all notifications for the logged-in user."""
    # pyrefly: ignore [missing-attribute]
    notifications = Notification.objects.filter(
        recipient=request.user
    ).values(
        'id', 'notification_type', 'title', 'message',
        'is_read', 'created_at', 'order_id'
    )
    return JsonResponse({
        'notifications': list(notifications),
        # pyrefly: ignore [missing-attribute]
        'unread_count': Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count(),
    })

@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Mark a single notification as read."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    notification.mark_as_read()
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read for the logged-in user."""
    # pyrefly: ignore [missing-attribute]
    updated = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    return JsonResponse({
        'status': 'ok',
        'marked': updated
    })
    
@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a single notification."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    notification.delete()
    return JsonResponse({'status': 'ok'})
    
def delete_all_notifications(request):
    """Delete all notifications for the logged-in user."""
    # pyrefly: ignore [missing-attribute]
    deleted = Notification.objects.filter(
        recipient=request.user,
    ).delete()
    return JsonResponse({
        'status': 'ok',
        'deleted': deleted
    })

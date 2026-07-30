from django.db.models import Sum
from .models import CartItem

def cart_count(request):
    if getattr(request, 'user', None) and request.user.is_authenticated and getattr(request.user, 'role', None) == 'student':
        # pyrefly: ignore [missing-attribute]
        count = CartItem.objects.filter(cart__student=request.user).aggregate(total=Sum('quantity'))['total']
        return {'cart_count': count or 0}
    return {'cart_count': 0}

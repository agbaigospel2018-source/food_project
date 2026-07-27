from .models import Cart


def cart_count(request):
    if getattr(request, 'user', None) and request.user.is_authenticated and request.user.role == 'student':
        cart = Cart.objects.filter(student=request.user).first()
        if cart:
            return {'cart_count': cart.total_items}
    return {'cart_count': 0}

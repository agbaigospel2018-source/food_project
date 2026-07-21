from django.db import models
from django.conf import settings

from menu.models import MenuItem

# Create your models here.
class Cart(models.Model):
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f'{self.student.username}\'s Cart'
    
    @property
    def total_amount(self):
        return sum(
            item.line_total
            for item in self.items.select_related('menu_item')
        )
        
    @property
    def total_items(self):
        return sum(
            item.quantity
            for item in self.items.all()
        )
    

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["cart", "menu_item"],
                name="unique_cart_menu_item",
            )
        ]

    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name}"

    @property
    def line_total(self):
        return self.menu_item.current_price * self.quantity
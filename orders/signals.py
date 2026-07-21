from django.db.models.signals import post_save, post_delete

from django.dispatch import receiver

from .models import OrderItem

@receiver(post_save, sender=OrderItem)
def update_order_total_after_save(sender, instance, **kwargs):
    
    """ 
    Recalculate the order total whenever am Orderitem is 
    created or updated
    """
    
    instance.order.update_total_amount()
    
    
@receiver(post_delete, sender=OrderItem)
def update_order_total_after_delete(sender, instance, **kwargs):
    """ 
    Recalculate the order total whenever an Orderitem is 
    deleted
    """
    
    instance.order.update_total_amount()
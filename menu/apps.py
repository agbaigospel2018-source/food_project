from django.apps import AppConfig


class MenuConfig(AppConfig):
    # pyrefly: ignore [bad-override]
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'menu'
    
    def ready(self):
        from . import signals

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    # pyrefly: ignore [bad-override]
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import notifications.signals

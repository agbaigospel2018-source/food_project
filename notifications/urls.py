from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_page, name='notifications_page'),
    path('api/list/', views.notification_list, name='notification_list'),
    path('<uuid:notification_id>/read/', views.mark_as_read, name='mark_read'),
    path('read-all/', views.mark_all_as_read, name='mark_all_read'),
    path('<uuid:notification_id>/delete/', views.delete_notification, name='delete'),
    path('delete-all/', views.delete_all_notifications, name='delete_all')
]

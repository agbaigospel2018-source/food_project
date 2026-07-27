from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    path("", views.MenuItemListView.as_view(), name="item_list"),
    path("availability/", views.availability_feed, name="availability_feed"),
    path("search-suggestions/", views.search_suggestions, name="search_suggestions"),
    path("vendors/<int:vendor_pk>/", views.MenuItemListView.as_view(), name="vendor_menu"),
    path("vendors/<int:vendor_pk>/<slug:slug>/", views.item_detail, name="item_detail"),
    path("items/<int:item_pk>/review/", views.upsert_review, name="upsert_review"),
    path("manage/vendors/<int:vendor_pk>/items/", views.VendorMenuItemListView.as_view(), name="vendor_items"),
    path("manage/vendors/<int:vendor_pk>/items/new/", views.VendorMenuItemCreateView.as_view(), name="vendor_item_create"),
    path("manage/vendors/<int:vendor_pk>/items/<int:pk>/edit/", views.VendorMenuItemUpdateView.as_view(), name="vendor_item_update"),
    path("manage/vendors/<int:vendor_pk>/items/<int:pk>/delete/", views.VendorMenuItemDeleteView.as_view(), name="vendor_item_delete"),
    path("manage/vendors/<int:vendor_pk>/items/<int:pk>/toggle/", views.toggle_item_availability, name="vendor_item_toggle"),
    path("manage/vendors/<int:vendor_pk>/categories/new/", views.VendorCategoryCreateView.as_view(), name="vendor_category_create"), 
]       

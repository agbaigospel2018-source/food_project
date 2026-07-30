from django.contrib import admin
from .models import Category, MenuItem, MenuItemOption, MenuItemOptionGroup, MenuItemReview, Mood, IngredientCategory, Ingredient, CustomBowl

class MenuItemOptionInline(admin.TabularInline):
    model = MenuItemOption
    extra = 1


class MenuItemOptionGroupInline(admin.StackedInline):
    model = MenuItemOptionGroup
    extra = 0
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ("name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ("name", "vendor", "category", "current_price", "is_active", "is_available", "stock_quantity", "average_rating")
    list_filter = ("is_active", "is_available", "is_featured", "is_vegetarian", "is_vegan", "is_halal", "vendor", "category")
    search_fields = ("name", "description", "vendor__business_name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("average_rating", "review_count")
    # pyrefly: ignore [bad-override-mutable-attribute]
    inlines = [MenuItemOptionGroupInline]


@admin.register(MenuItemOptionGroup)
class MenuItemOptionGroupAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ("name", "item", "choice_type", "is_required", "min_choices", "max_choices")
    # pyrefly: ignore [bad-override-mutable-attribute]
    inlines = [MenuItemOptionInline]


@admin.register(MenuItemReview)
class MenuItemReviewAdmin(admin.ModelAdmin):
    # pyrefly: ignore [bad-override-mutable-attribute]
    list_display = ("item", "student", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved", "created_at")
    search_fields = ("item__name", "student__username", "comment")


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "max_selectable_items", "display_order")
    ordering = ("display_order",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "calories", "protein", "carbs", "fats")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(CustomBowl)
class CustomBowlAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "base_menu_item")
    search_fields = ("user__username", "base_menu_item__name")

from django.db import models, transaction
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
# Create your models here.

def vendor_model_label():
    return getattr(settings, "MENU_VENDOR_MODEL", "vendors.Vendor")


class ActiveMenuItemQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_active=True)

    def available_now(self):
        return [item for item in self.public() if item.is_available_now]


class Category(models.Model):
    vendor = models.ForeignKey(vendor_model_label(), on_delete=models.CASCADE, related_name="menu_categories")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["vendor", "slug"], name="unique_menu_category_slug_per_vendor"),
        ]
        verbose_name_plural = "categories"

    def __str__(self):
        return f"{self.vendor} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    vendor = models.ForeignKey(vendor_model_label(), on_delete=models.CASCADE, related_name="menu_items")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="menu/items/", blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    prep_time_minutes = models.PositiveIntegerField(default=15)
    calories = models.PositiveIntegerField(blank=True, null=True)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_halal = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(blank=True, null=True)
    available_from = models.TimeField(blank=True, null=True)
    available_until = models.TimeField(blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    review_count = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveMenuItemQuerySet.as_manager()

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["vendor", "slug"], name="unique_menu_item_slug_per_vendor"),
        ]
        indexes = [
            models.Index(fields=["vendor", "is_active", "is_available"]),
            models.Index(fields=["is_featured", "average_rating"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.vendor})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        if self.discount_price is not None and self.discount_price > self.base_price:
            raise ValidationError({"discount_price": "Discount price cannot be greater than base price."})
        if self.category and self.category.vendor_id != self.vendor_id:
            raise ValidationError({"category": "Category must belong to the same vendor as the menu item."})

    def get_absolute_url(self):
        return reverse("menu:item_detail", kwargs={"vendor_pk": self.vendor_id, "slug": self.slug})

    @property
    def current_price(self):
        return self.discount_price if self.discount_price is not None else self.base_price

    @property
    def is_in_stock(self):
        return self.stock_quantity is None or self.stock_quantity > 0

    @property
    def is_within_service_time(self):
        if not self.available_from or not self.available_until:
            return True
        now = timezone.localtime().time()
        if self.available_from <= self.available_until:
            return self.available_from <= now <= self.available_until
        return now >= self.available_from or now <= self.available_until

    @property
    def is_available_now(self):
        return self.is_active and self.is_available and self.is_in_stock and self.is_within_service_time

    @property
    def availability_label(self):
        if not self.is_active:
            return "Hidden"
        if not self.is_available:
            return "Unavailable"
        if not self.is_in_stock:
            return "Sold out"
        if not self.is_within_service_time:
            return "Outside service time"
        return "Available"

    def refresh_rating_cache(self):
        stats = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"), count=Count("id"))
        self.average_rating = stats["avg"] or Decimal("0.00")
        self.review_count = stats["count"] or 0
        self.save(update_fields=["average_rating", "review_count", "updated_at"])


class MenuItemOptionGroup(models.Model):
    SINGLE = "single"
    MULTIPLE = "multiple"
    CHOICE_TYPES = ((SINGLE, "Single choice"), (MULTIPLE, "Multiple choice"))

    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="option_groups")
    name = models.CharField(max_length=120)
    choice_type = models.CharField(max_length=12, choices=CHOICE_TYPES, default=SINGLE)
    is_required = models.BooleanField(default=False)
    min_choices = models.PositiveIntegerField(default=0)
    max_choices = models.PositiveIntegerField(default=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.item.name} - {self.name}"

    def clean(self):
        if self.choice_type == self.SINGLE and self.max_choices != 1:
            raise ValidationError({"max_choices": "Single choice groups must allow exactly one choice."})
        if self.min_choices > self.max_choices:
            raise ValidationError({"min_choices": "Minimum choices cannot exceed maximum choices."})
        if self.is_required and self.min_choices == 0:
            raise ValidationError({"min_choices": "Required groups must have at least one minimum choice."})


class MenuItemOption(models.Model):
    group = models.ForeignKey(MenuItemOptionGroup, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    is_available = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


# class Cart(models.Model):
#     ACTIVE = "active"
#     ORDERED = "ordered"
#     ABANDONED = "abandoned"
#     STATUS_CHOICES = ((ACTIVE, "Active"), (ORDERED, "Ordered"), (ABANDONED, "Abandoned"))

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="menu_carts")
#     session_key = models.CharField(max_length=40, blank=True, db_index=True)
#     status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ACTIVE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["session_key", "status"])]

#     def __str__(self):
#         owner = self.user or self.session_key or "anonymous"
#         return f"Cart {self.pk} - {owner}"

#     @classmethod
#     def for_request(cls, request):
#         if request.user.is_authenticated:
#             cart = cls.objects.filter(user=request.user, status=cls.ACTIVE).first()
#             if cart:
#                 return cart
#             cart = cls.objects.create(user=request.user, status=cls.ACTIVE, session_key=request.session.session_key or "")
#             return cart
#         if not request.session.session_key:
#             request.session.create()
#         cart = cls.objects.filter(session_key=request.session.session_key, status=cls.ACTIVE, user=None).first()
#         if cart:
#             return cart
#         cart = cls.objects.create(session_key=request.session.session_key, status=cls.ACTIVE, user=None)
#         return cart

#     @property
#     def total_quantity(self):
#         return sum(item.quantity for item in self.items.select_related("menu_item"))

#     @property
#     def subtotal(self):
#         return sum((item.line_total for item in self.items.prefetch_related("selected_options")), Decimal("0.00"))

#     def add_item(self, menu_item, quantity=1, option_ids=None, note=""):
#         if not menu_item.is_available_now:
#             raise ValidationError(f"{menu_item.name} is currently {menu_item.availability_label.lower()}.")
#         if menu_item.stock_quantity is not None and quantity > menu_item.stock_quantity:
#             raise ValidationError(f"Only {menu_item.stock_quantity} {menu_item.name} left.")

#         option_ids = [int(option_id) for option_id in (option_ids or [])]
#         selected_options = list(
#             MenuItemOption.objects.select_related("group", "group__item")
#             .filter(id__in=option_ids, group__item=menu_item, is_available=True)
#         )
#         if len(selected_options) != len(set(option_ids)):
#             raise ValidationError("One or more selected options are invalid or unavailable.")
#         self._validate_options(menu_item, selected_options)

#         with transaction.atomic():
#             candidate_items = self.items.filter(menu_item=menu_item, note=note).prefetch_related("selected_options")
#             selected_ids = set(option_ids)
#             for cart_item in candidate_items:
#                 if set(cart_item.selected_options.values_list("id", flat=True)) == selected_ids:
#                     if menu_item.stock_quantity is not None and cart_item.quantity + quantity > menu_item.stock_quantity:
#                         raise ValidationError(f"Only {menu_item.stock_quantity} {menu_item.name} left.")
#                     cart_item.quantity += quantity
#                     cart_item.full_clean()
#                     cart_item.save(update_fields=["quantity", "updated_at"])
#                     return cart_item

#             cart_item = self.items.create(
#                 menu_item=menu_item,
#                 vendor=menu_item.vendor,
#                 quantity=quantity,
#                 unit_price=menu_item.current_price,
#                 note=note,
#             )
#             cart_item.selected_options.set(selected_options)
#             return cart_item

#     def _validate_options(self, menu_item, selected_options):
#         selected_by_group = {}
#         for option in selected_options:
#             selected_by_group.setdefault(option.group_id, []).append(option)

#         for group in menu_item.option_groups.prefetch_related("options"):
#             count = len(selected_by_group.get(group.id, []))
#             if group.is_required and count < group.min_choices:
#                 raise ValidationError(f"Choose at least {group.min_choices} option(s) for {group.name}.")
#             if count > group.max_choices:
#                 raise ValidationError(f"Choose no more than {group.max_choices} option(s) for {group.name}.")


# class CartItem(models.Model):
#     cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
#     menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="cart_items")
#     vendor = models.ForeignKey(vendor_model_label(), on_delete=models.CASCADE, related_name="cart_items")
#     selected_options = models.ManyToManyField(MenuItemOption, blank=True, related_name="cart_items")
#     quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(99)])
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)
#     note = models.CharField(max_length=255, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ["created_at"]

#     def __str__(self):
#         return f"{self.quantity} x {self.menu_item.name}"

#     def clean(self):
#         if self.menu_item.vendor_id != self.vendor_id:
#             raise ValidationError({"vendor": "Cart item vendor must match the menu item vendor."})
#         if self.quantity < 1:
#             raise ValidationError({"quantity": "Quantity must be at least 1."})

#     @property
#     def options_total(self):
#         return sum((option.price_delta for option in self.selected_options.all()), Decimal("0.00"))

#     @property
#     def line_total(self):
#         return (self.unit_price + self.options_total) * self.quantity


class MenuItemReview(models.Model):
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="reviews")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="menu_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=120, blank=True)
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["item", "student"], name="unique_review_per_student_per_menu_item"),
        ]

    def __str__(self):
        return f"{self.item.name}: {self.rating}/5"

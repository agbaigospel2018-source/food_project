from django.db import models, transaction
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

def vendor_model_label():
    return getattr(settings, "MENU_VENDOR_MODEL", "vendors.Vendor")

class ActiveMenuItemQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_active=True)

    def available_now(self):
        return [item for item in self.public() if item.is_available_now]



class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, blank=True, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    # pyrefly: ignore [bad-override]
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # pyrefly: ignore [bad-assignment]
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
    is_customizable = models.BooleanField(default=False)
    moods = models.ManyToManyField('Mood', blank=True, related_name="menu_items_original")
    base_ingredients = models.ManyToManyField('Ingredient', blank=True, related_name="menu_items_original")
    stock_quantity = models.PositiveIntegerField(blank=True, null=True)
    available_from = models.TimeField(blank=True, null=True)
    available_until = models.TimeField(blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    review_count = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # pyrefly: ignore [bad-argument-type]
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
            # pyrefly: ignore [bad-assignment]
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        if self.discount_price is not None and self.discount_price > self.base_price:
            raise ValidationError({"discount_price": "Discount price cannot be greater than base price."})

    def get_absolute_url(self):
        # pyrefly: ignore [missing-attribute]
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
            return "Closed"
        return "Available"

    def refresh_rating_cache(self):
        # pyrefly: ignore [missing-attribute]
        stats = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"), count=Count("id"))
        # pyrefly: ignore [bad-assignment]
        self.average_rating = stats["avg"] or Decimal("0.00")
        # pyrefly: ignore [bad-assignment]
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

    # pyrefly: ignore [bad-override]
    def __str__(self):
        return self.name

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

class Mood(models.Model):
    """Handles menu filtration contexts (e.g., 'Post-Workout Fuel', 'Late Night Comfort')"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='mood_icons/', blank=True, null=True)

    def __str__(self) -> str:
        # pyrefly: ignore [bad-return]
        return self.name


class IngredientCategory(models.Model):
    """Defines structural steps for the custom builder (e.g., Base, Protein, Veggies)"""
    name = models.CharField(max_length=100)
    max_selectable_items = models.PositiveIntegerField(default=1)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']
        verbose_name_plural = "Ingredient Categories"

    def __str__(self) -> str:
        # pyrefly: ignore [bad-return]
        return self.name


class Ingredient(models.Model):
    """Individual building blocks for custom creations complete with macro data"""
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        IngredientCategory, 
        on_delete=models.CASCADE, 
        related_name='ingredients'
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    
    # Nutritional Macros
    calories = models.PositiveIntegerField(default=0)
    protein = models.FloatField(default=0.0)  # In grams
    carbs = models.FloatField(default=0.0)    # In grams
    fats = models.FloatField(default=0.0)     # In grams

    def __str__(self) -> str:
        return f"{self.name} ({self.category.name})"

    def __str__(self) -> str:
        return f"{self.name} ({self.category.name})"


class CustomBowl(models.Model):
    """Stores the specific customized matrix built interactively by a user"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='custom_bowls'
    )
    base_menu_item = models.ForeignKey(
        MenuItem, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='customizations'
    )
    selected_ingredients = models.ManyToManyField(Ingredient, related_name='custom_bowls_selected')

    def __str__(self) -> str:
        user_str = self.user.username if self.user else "Guest"
        item_str = f" based on {self.base_menu_item.name}" if self.base_menu_item else ""
        return f"Custom Bowl ({user_str}){item_str}"

    # --- Macro Calculation Logic ---
    # Database level aggregations prevent dragging large QuerySets into memory loop structures.
    @property
    def total_price(self) -> Decimal:
        if hasattr(self, '_total_price'):
            return self._total_price
        base = self.base_menu_item.base_price if self.base_menu_item else Decimal('0.00')
        # pyrefly: ignore [missing-attribute]
        ingredient_total = self.selected_ingredients.aggregate(total=models.Sum('price'))['total'] or Decimal('0.00')
        # pyrefly: ignore [unsupported-operation]
        return base + ingredient_total

    @property
    def total_calories(self) -> int:
        if hasattr(self, '_total_calories'):
            return self._total_calories
        return self.selected_ingredients.aggregate(total=models.Sum('calories'))['total'] or 0

    @property
    def total_protein(self) -> float:
        if hasattr(self, '_total_protein'):
            return self._total_protein
        return self.selected_ingredients.aggregate(total=models.Sum('protein'))['total'] or 0.0

    @property
    def total_carbs(self) -> float:
        if hasattr(self, '_total_carbs'):
            return self._total_carbs
        return self.selected_ingredients.aggregate(total=models.Sum('carbs'))['total'] or 0.0

    @property
    def total_fats(self) -> float:
        if hasattr(self, '_total_fats'):
            return self._total_fats
        return self.selected_ingredients.aggregate(total=models.Sum('fats'))['total'] or 0.0



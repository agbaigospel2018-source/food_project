from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.utils.html import escape
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CategoryForm, IngredientCategoryForm, IngredientForm, MenuItemForm, ReviewForm
from .models import Category, Ingredient, IngredientCategory, MenuItem, MenuItemReview
from .utils import get_managed_vendor_or_403, get_vendor_model
# pyrefly: ignore [missing-import]
from rest_framework import viewsets
from .serializers import MoodSerializer, IngredientCategorySerializer, IngredientSerializer, MenuItemSerializer, CustomBowlSerializer


class MenuItemListView(ListView):
    model = MenuItem
    template_name = "menu/menu_item_list.html"
    context_object_name = "items"
    paginate_by = 24

    def get_queryset(self):
        queryset = (
            MenuItem.objects.public()
            .select_related("vendor", "category")
            .prefetch_related("option_groups__options")
        )
        self.vendor = None

        vendor_pk = self.kwargs.get("vendor_pk") or self.request.GET.get("vendor")
        if vendor_pk:
            self.vendor = get_object_or_404(get_vendor_model(), pk=vendor_pk)
            queryset = queryset.filter(vendor=self.vendor)

        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                # pyrefly: ignore [unsupported-operation]
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(vendor__business_name__icontains=query)
            )

        for flag in ("is_vegetarian", "is_vegan", "is_halal", "is_spicy"):
            if self.request.GET.get(flag) == "1":
                queryset = queryset.filter(**{flag: True})

        if self.request.GET.get("available") == "1":
            item_ids = [item.id for item in queryset if item.is_available_now]
            queryset = queryset.filter(id__in=item_ids)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vendor"] = self.vendor
        # pyrefly: ignore [missing-attribute]
        context["categories"] = Category.objects.filter(is_active=True)
        return context


def item_detail(request, vendor_pk, slug):
    item = get_object_or_404(
        MenuItem.objects.public()
        .select_related("vendor", "category")
        .prefetch_related("option_groups__options", "reviews__student"),
        vendor_id=vendor_pk,
        slug=slug, 
    )
    review = None
    if request.user.is_authenticated:
        # pyrefly: ignore [missing-attribute]
        review = MenuItemReview.objects.filter(item=item, student=request.user).first()

    return render(
        request,
        "menu/menu_item_detail.html",
        {
            "item": item,
            "review_form": ReviewForm(instance=review),
            "reviews": item.reviews.filter(is_approved=True).select_related("student"),
        },
    )


@login_required
@require_POST
def upsert_review(request, item_pk):
    item = get_object_or_404(MenuItem.objects.public(), pk=item_pk)
    # pyrefly: ignore [missing-attribute]
    review = MenuItemReview.objects.filter(item=item, student=request.user).first()
    form = ReviewForm(request.POST, instance=review)
    if form.is_valid():
        review = form.save(commit=False)
        review.item = item
        review.student = request.user
        review.save()
        messages.success(request, "Thanks for reviewing this item.")
    else:
        messages.error(request, "Please fix your review and try again.")
    return redirect(item.get_absolute_url())


def availability_feed(request):
    item_ids = request.GET.getlist("item")
    queryset = MenuItem.objects.public().select_related("vendor")
    if item_ids:
        queryset = queryset.filter(id__in=item_ids)

    payload = [
        {
            "id": item.id,
            "name": item.name,
            "vendor_id": item.vendor_id,
            "available": item.is_available_now,
            "label": item.availability_label,
            "stock_quantity": item.stock_quantity,
            "updated_at": item.updated_at.isoformat(),
        }
        for item in queryset[:100]
    ]
    return JsonResponse({"items": payload})


def search_suggestions(request):
    query = (request.GET.get("q") or "").strip()
    suggestions = []

    if query:
        items = (
            MenuItem.objects.public()
            .select_related("vendor")
            .filter(
                # pyrefly: ignore [unsupported-operation]
                Q(name__icontains=query) | Q(description__icontains=query) | Q(vendor__business_name__icontains=query)
            )[:8]
        )
        for item in items:
            suggestions.append(
                {
                    "type": "item",
                    "label": item.name,
                    "value": item.name,
                    "url": item.get_absolute_url(),
                    "meta": item.vendor.business_name,
                }
            )

        vendors = (
            get_vendor_model()
            .objects.filter(business_name__icontains=query)[:6]
        )
        for vendor in vendors:
            suggestions.append(
                {
                    "type": "vendor",
                    "label": vendor.business_name,
                    "value": vendor.business_name,
                    "url": reverse("menu:vendor_menu", kwargs={"vendor_pk": vendor.pk}),
                    "meta": "Restaurant",
                }
            )

    return JsonResponse({"suggestions": suggestions})


class VendorMenuMixin(LoginRequiredMixin):
    vendor = None

    def dispatch(self, request, *args, **kwargs):
        self.vendor = get_managed_vendor_or_403(request.user, kwargs["vendor_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # pyrefly: ignore [missing-attribute]
        context = super().get_context_data(**kwargs)
        context["vendor"] = self.vendor
        return context


class VendorMenuItemListView(VendorMenuMixin, ListView):
    template_name = "menu/management/item_list.html"
    context_object_name = "items"

    def get_queryset(self):
        return MenuItem.objects.filter(vendor=self.vendor).select_related("category")


class VendorMenuItemCreateView(VendorMenuMixin, CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "menu/management/item_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["vendor"] = self.vendor
        kwargs["instance"] = MenuItem(vendor=self.vendor)
        return kwargs

    def form_valid(self, form):
        form.instance.vendor = self.vendor
        messages.success(self.request, "Menu item created.")
        return super().form_valid(form)

    def get_success_url(self):
        # pyrefly: ignore [missing-attribute]
        return reverse("menu:vendor_items", kwargs={"vendor_pk": self.vendor.pk})


class VendorMenuItemUpdateView(VendorMenuMixin, UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "menu/management/item_form.html"

    def get_queryset(self):
        return MenuItem.objects.filter(vendor=self.vendor)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["vendor"] = self.vendor
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Menu item updated.")
        return super().form_valid(form)

    def get_success_url(self):
        # pyrefly: ignore [missing-attribute]
        return reverse("menu:vendor_items", kwargs={"vendor_pk": self.vendor.pk})


class VendorMenuItemDeleteView(VendorMenuMixin, DeleteView):
    model = MenuItem
    template_name = "menu/management/item_confirm_delete.html"

    def get_queryset(self):
        return MenuItem.objects.filter(vendor=self.vendor)

    def get_success_url(self):
        messages.success(self.request, "Menu item deleted.")
        # pyrefly: ignore [missing-attribute]
        return reverse("menu:vendor_items", kwargs={"vendor_pk": self.vendor.pk})


@require_POST
@login_required
def toggle_item_availability(request, vendor_pk, pk):
    vendor = get_managed_vendor_or_403(request.user, vendor_pk)
    item = get_object_or_404(MenuItem, pk=pk, vendor=vendor)
    item.is_available = not item.is_available
    item.save(update_fields=["is_available", "updated_at"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "available": item.is_available_now, "label": item.availability_label})
    return redirect("menu:vendor_items", vendor_pk=vendor.pk)


class VendorCategoryCreateView(VendorMenuMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "menu/management/category_form.html"

    def form_valid(self, form):
        form.instance.vendor = self.vendor
        messages.success(self.request, "Category created.")
        return super().form_valid(form)

    def get_success_url(self):
        # pyrefly: ignore [missing-attribute]
        return reverse("menu:vendor_items", kwargs={"vendor_pk": self.vendor.pk})

# ─── Vendor Crave Bowl Management ───

class VendorCraveBowlManageView(VendorMenuMixin, ListView):
    template_name = "menu/management/crave_bowl_manage.html"
    context_object_name = "categories"

    def get_queryset(self):
        return IngredientCategory.objects.filter(vendor=self.vendor).prefetch_related("ingredients")


class VendorIngredientCategoryCreateView(VendorMenuMixin, CreateView):
    model = IngredientCategory
    form_class = IngredientCategoryForm
    template_name = "menu/management/ingredient_category_form.html"

    def form_valid(self, form):
        form.instance.vendor = self.vendor
        messages.success(self.request, "Category created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("menu:vendor_crave_bowl", kwargs={"vendor_pk": self.vendor.pk})


class VendorIngredientCategoryUpdateView(VendorMenuMixin, UpdateView):
    model = IngredientCategory
    form_class = IngredientCategoryForm
    template_name = "menu/management/ingredient_category_form.html"

    def get_queryset(self):
        return IngredientCategory.objects.filter(vendor=self.vendor)

    def form_valid(self, form):
        messages.success(self.request, "Category updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("menu:vendor_crave_bowl", kwargs={"vendor_pk": self.vendor.pk})


class VendorIngredientCategoryDeleteView(VendorMenuMixin, DeleteView):
    model = IngredientCategory
    template_name = "menu/management/ingredient_category_confirm_delete.html"

    def get_queryset(self):
        return IngredientCategory.objects.filter(vendor=self.vendor)

    def get_success_url(self):
        messages.success(self.request, "Category deleted.")
        return reverse("menu:vendor_crave_bowl", kwargs={"vendor_pk": self.vendor.pk})


class VendorIngredientCreateView(VendorMenuMixin, CreateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = "menu/management/ingredient_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["vendor"] = self.vendor
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Ingredient added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("menu:vendor_crave_bowl", kwargs={"vendor_pk": self.vendor.pk})


class VendorIngredientUpdateView(VendorMenuMixin, UpdateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = "menu/management/ingredient_form.html"

    def get_queryset(self):
        return Ingredient.objects.filter(category__vendor=self.vendor)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["vendor"] = self.vendor
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Ingredient updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("menu:vendor_crave_bowl", kwargs={"vendor_pk": self.vendor.pk})


class VendorIngredientDeleteView(VendorMenuMixin, DeleteView):
    model = Ingredient
    template_name = "menu/management/ingredient_confirm_delete.html"

    def get_queryset(self):
        return Ingredient.objects.filter(category__vendor=self.vendor)

    def get_success_url(self):
        messages.success(self.request, "Ingredient deleted.")
        return reverse("menu:vendor_crave_bowl", kwargs={"vendor_pk": self.vendor.pk})


def crave_bowl_view(request, vendor_pk):
    vendor = get_object_or_404(get_vendor_model(), pk=vendor_pk)
    return render(request, "menu/crave_bowl.html", {"vendor": vendor})

class MoodViewSet(viewsets.ReadOnlyModelViewSet):
    from .models import Mood
    # pyrefly: ignore [missing-attribute]
    queryset = Mood.objects.all()
    serializer_class = MoodSerializer

class IngredientCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    from .models import IngredientCategory
    # pyrefly: ignore [missing-attribute]
    queryset = IngredientCategory.objects.all()
    serializer_class = IngredientCategorySerializer

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    from .models import Ingredient
    # pyrefly: ignore [missing-attribute]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        queryset = (
            MenuItem.objects.public()
            .select_related("vendor", "category")
            .prefetch_related("moods", "base_ingredients")
        )
        vendor_pk = self.request.query_params.get("vendor")
        if vendor_pk:
            queryset = queryset.filter(vendor_id=vendor_pk)
            
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
            
        return queryset

class CustomBowlViewSet(viewsets.ModelViewSet):
    from .models import CustomBowl
    serializer_class = CustomBowlSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            # pyrefly: ignore [unknown-name]
            return CustomBowl.objects.filter(user=self.request.user)
        # pyrefly: ignore [unknown-name]
        return CustomBowl.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# pyrefly: ignore [missing-import]
from rest_framework.generics import ListAPIView
# pyrefly: ignore [missing-import]
from rest_framework.views import APIView
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework import status

class IngredientCategoryListAPIView(ListAPIView):
    from .models import IngredientCategory
    serializer_class = IngredientCategorySerializer

    def get_queryset(self):
        from .models import IngredientCategory
        queryset = IngredientCategory.objects.all()
        vendor_id = self.request.query_params.get("vendor")
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        return queryset

class AddCustomBowlToCartAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Create CustomBowl
        serializer = CustomBowlSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            bowl = serializer.save(user=request.user)
            
            # Assuming cart app has a way to add CustomBowl
            # You might need to adjust this depending on the cart app's models
            from cart.models import Cart
            # pyrefly: ignore [missing-attribute]
            cart, _ = Cart.objects.get_or_create(student=request.user)
            # if CartItem doesn't natively support CustomBowl, this might need more logic
            # Just returning the created bowl for now
            return Response(CustomBowlSerializer(bowl).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


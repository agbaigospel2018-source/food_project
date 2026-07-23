from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CategoryForm, MenuItemForm, ReviewForm
from .models import Category, MenuItem, MenuItemReview
from .utils import get_managed_vendor_or_403, get_vendor_model


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
        if self.vendor:
            context["categories"] = Category.objects.filter(vendor=self.vendor, is_active=True)
        else:
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


class VendorMenuMixin(LoginRequiredMixin):
    vendor = None

    def dispatch(self, request, *args, **kwargs):
        self.vendor = get_managed_vendor_or_403(request.user, kwargs["vendor_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
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
        return reverse("menu:vendor_items", kwargs={"vendor_pk": self.vendor.pk})


class VendorMenuItemDeleteView(VendorMenuMixin, DeleteView):
    model = MenuItem
    template_name = "menu/management/item_confirm_delete.html"

    def get_queryset(self):
        return MenuItem.objects.filter(vendor=self.vendor)

    def get_success_url(self):
        messages.success(self.request, "Menu item deleted.")
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
        return reverse("menu:vendor_items", kwargs={"vendor_pk": self.vendor.pk})

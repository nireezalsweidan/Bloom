from decimal import Decimal, InvalidOperation

from django.db.models import Q, Count
from django.views.generic import ListView, DetailView

from .models import Item, Category, Tag


class ItemListView(ListView):
    model = Item
    template_name = "catalog/item_list.html"
    context_object_name = "items"
    paginate_by = 9

    def get_queryset(self):
        queryset = Item.objects.filter(is_available=True).select_related("category").prefetch_related("tags")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        category_slugs = self.request.GET.getlist("category")
        if category_slugs:
            queryset = queryset.filter(category__slug__in=category_slugs)

        tag_slugs = self.request.GET.getlist("tag")
        if tag_slugs:
            for slug in tag_slugs:
                queryset = queryset.filter(tags__slug=slug)
            queryset = queryset.distinct()

        min_price = self.request.GET.get("min_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=Decimal(min_price))
            except (InvalidOperation, ValueError):
                pass

        max_price = self.request.GET.get("max_price")
        if max_price:
            try:
                queryset = queryset.filter(price__lte=Decimal(max_price))
            except (InvalidOperation, ValueError):
                pass

        if self.request.GET.get("in_stock"):
            queryset = queryset.filter(stock_quantity__gt=0)

        sort = self.request.GET.get("sort")
        if sort == "price_asc":
            queryset = queryset.order_by("price")
        elif sort == "price_desc":
            queryset = queryset.order_by("-price")
        elif sort == "newest":
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.annotate(
            item_count=Count("items", filter=Q(items__is_available=True))
        )
        context["tags"] = Tag.objects.all()
        context["selected_categories"] = self.request.GET.getlist("category")
        context["selected_tags"] = self.request.GET.getlist("tag")
        context["query"] = self.request.GET.get("q", "")
        context["min_price"] = self.request.GET.get("min_price", "")
        context["max_price"] = self.request.GET.get("max_price", "")
        context["in_stock_only"] = self.request.GET.get("in_stock", "")
        context["sort"] = self.request.GET.get("sort", "")

        params = self.request.GET.copy()
        params.pop("page", None)
        context["base_qs"] = params.urlencode()
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = "catalog/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return Item.objects.filter(is_available=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_items"] = (
            Item.objects.filter(category=self.object.category, is_available=True)
            .exclude(pk=self.object.pk)[:3]
        )
        return context
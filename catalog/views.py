from django.views.generic import ListView, DetailView
from django.db.models import Q

from .models import Item, Category, Tag


class ItemListView(ListView):
    model = Item
    template_name = "catalog/item_list.html"
    context_object_name = "items"
    paginate_by = 12

    def get_queryset(self):
        queryset = Item.objects.filter(is_available=True).select_related("category").prefetch_related("tags")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        category_slug = self.request.GET.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        tag_slugs = self.request.GET.getlist("tag")
        if tag_slugs:
            for slug in tag_slugs:
                queryset = queryset.filter(tags__slug=slug)
            queryset = queryset.distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["tags"] = Tag.objects.all()
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_tags"] = self.request.GET.getlist("tag")
        context["query"] = self.request.GET.get("q", "")
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = "catalog/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return Item.objects.filter(is_available=True)
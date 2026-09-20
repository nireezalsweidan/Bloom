from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)   # matches ERD's CATEGORY.description

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Corresponds to the ERD's ITEM entity. Covers flowers, bouquets,
    greeting cards, and gifts — the category (Flowers/Bouquets/Gifts/
    Greeting Cards) distinguishes the kind of item, so there's no
    separate product_type field.
    """
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="items/", blank=True, null=True)

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items")
    tags = models.ManyToManyField(Tag, blank=True, related_name="items")  # ERD's ITEM_TAG junction

    stock_quantity = models.PositiveIntegerField(default=0)  # placeholder until the Inventory epic
    is_available = models.BooleanField(default=True)         # not in ERD, kept as a bookkeeping field

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Item.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:item_detail", kwargs={"slug": self.slug})

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    def __str__(self):
        return self.name
from django.db import models


class AddressManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('customer')


class ColourInventoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('product', 'colour')


class FavoriteProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'product')


class OrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'address')


class OrderItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'order', 'product')


class ProductManager(models.Manager):
    def get_queryset(self):
        return super() \
            .get_queryset() \
            .prefetch_related(
                'category',
                'product_reviews',
                'size_inventory',
                'color_inventory',
                'images'
        ) \
            .filter(inventory__gt=0)


class ProductReviewManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'product')


class SizeInventoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('product', 'size')

from django.contrib import admin, messages
from django.utils.html import mark_safe

from store.models import *

# Register your models here.
admin.site.register((Size, ItemLocation,))


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "gender", "products_count",)
    list_filter = ("title", "gender",)
    ordering = ("title", "gender",)

    @staticmethod
    @admin.display(ordering='products_count')
    def products_count(obj):
        return obj.products.count()


@admin.register(Colour)
class ColourAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_code",)
    list_filter = ("name", "hex_code",)
    ordering = ("name",)
    search_fields = ("name", "hex_code",)


class InventoryFilter(admin.SimpleListFilter):
    title = "inventory"
    parameter_name = "inventory"

    def lookups(self, request, model_admin):
        return [("<10", "Low")]

    def queryset(self, request, queryset):
        if self.value() == "<10":
            return queryset.filter(inventory__lt=10)


class ProductImageAdmin(admin.TabularInline):
    model = ProductImage
    extra = 2
    max_num = 3


class ProductColorSizeInventoryInline(admin.TabularInline):
    model = ProductColorSizeInventory
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = (ProductImageAdmin, ProductColorSizeInventoryInline,)
    list_display = (
        "title",
        "category",
        "price",
        "percentage_off",
        "discount_price",
        "average_ratings",
        "inventory_status",
    )
    list_filter = (
        "category",
        "condition",
        "percentage_off",
        InventoryFilter
    )
    list_per_page = 30
    list_select_related = ("category",)
    ordering = ("title", "category", "percentage_off",)
    readonly_fields = ("product_images",)
    search_fields = ("title", "category__name",)

    @admin.display(ordering="inventory")
    def inventory_status(self, obj):
        if obj.inventory < 10:
            return "Low"
        return "High"

    @staticmethod
    def product_images(obj):
        product_images = obj.images.all()
        html = ''
        for product in product_images:
            html += '<img src="{url}" width="{width}" height="{height}" />'.format(
                    url=product.image.url,
                    width=300,
                    height=200,
            )
        return mark_safe(html)

    @admin.action(description="Clear inventory")
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
                request,
                f"{updated_count} products were successfully updated.",
                messages.ERROR, )


@admin.register(FavoriteProduct)
class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ("customer", "product",)
    list_filter = ("product__category",)
    list_per_page = 30
    list_select_related = ("product",)
    ordering = ("customer", "product",)
    search_fields = ("customer__full_name", "product__name",)


@admin.register(SliderImage)
class SliderImageAdmin(admin.ModelAdmin):
    list_display = ('image_id',)

    def image_id(self, obj):
        return f"Image {str(obj.id)[:5]}"


class ProductReviewImageAdmin(admin.TabularInline):
    model = ProductReviewImage
    extra = 2
    max_num = 3


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    inlines = (ProductReviewImageAdmin,)
    list_display = ("product", "customer", "ratings",)
    list_filter = ("product__title", "product__category",)
    list_per_page = 30
    list_select_related = ("product__category",)
    ordering = ("customer", "ratings",)
    readonly_fields = ("product_review_images",)
    search_fields = ("product__title",)

    def product_review_images(self, obj):
        product_review_images = obj.product_review_images.all()
        html = ''
        for product_review in product_review_images:
            html += '<img src="{url}" width="{width}" height="{height}" />'.format(
                    url=product_review.image.url,
                    width=product_review.image.width,
                    height=product_review.image.height,
            )
        return mark_safe(html)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "notification_type", "general",)
    list_filter = ("notification_type", "general",)
    list_per_page = 20
    ordering = ("title", "notification_type",)
    search_fields = ("title",)


@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "price", "expired",)
    list_filter = ("expired", "price",)
    list_per_page = 20
    ordering = ("code", "expired",)
    search_fields = ("price",)


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ["product"]
    min_num = 1
    max_num = 10
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ("customer", "transaction_ref", "payment_status", "shipping_status", "placed_at",)
    list_filter = ("payment_status", "shipping_status",)
    list_per_page = 30
    ordering = ("customer", "transaction_ref", "payment_status", "shipping_status", "placed_at",)
    search_fields = ("customer__full_name", "transaction_ref", "payment_status", "shipping_status")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code",)
    list_per_page = 20
    ordering = ("name",)
    search_fields = ("name__istartswith", "code",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("customer", "first_name", "last_name", "country", "city", "zip_code")
    list_filter = ("country", "city", "zip_code", "customer")
    list_per_page = 20
    list_select_related = ["country"]
    ordering = ("country__name", "city", "first_name")
    search_fields = ("first_name__istartswith", "last_name__istartswith", "country__name")

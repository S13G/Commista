import secrets
from uuid import uuid4

from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg
from django.utils import timezone
from django.utils.functional import cached_property

from common.models import BaseModel
from core.validators import validate_phone_number
from store.choices import (CONDITION_CHOICES, GENDER_CHOICES, NOTIFICATION_CHOICES, PAYMENT_PENDING, PAYMENT_STATUS,
                           RATING_CHOICES, SHIPPING_STATUS_CHOICES, SHIPPING_STATUS_PENDING)
from store.validators import validate_image_size

# Create your models here.

Customer = get_user_model()


class Category(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ('-created',)

    def __str__(self):
        return self.title


class Size(BaseModel):
    title = models.CharField(max_length=5, unique=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title


class Colour(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    hex_code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.name} ---- {self.hex_code}"


class ItemLocation(BaseModel):
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.location


class ProductsManager(models.Manager):
    def get_queryset(self):
        return super(ProductsManager, self).get_queryset().prefetch_related('category', 'product_reviews', 'size',
                                                                            'colour', 'images').filter(inventory__lt=10)


class Product(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(
            populate_from="title", unique=True, always_update=True, editable=False
    )
    category = models.ForeignKey(
            Category, on_delete=models.CASCADE, related_name="products"
    )
    description = models.TextField()
    style = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    percentage_off = models.PositiveIntegerField(default=0)
    condition = models.CharField(max_length=2, choices=CONDITION_CHOICES)
    location = models.ForeignKey(ItemLocation, on_delete=models.SET_NULL, null=True, blank=False,
                                 related_name="products", )
    flash_sale_start_date = models.DateTimeField(null=True, blank=True)
    flash_sale_end_date = models.DateTimeField(null=True, blank=True)
    objects = models.Manager()
    categorized = ProductsManager()

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.title} --- {self.category}"

    @cached_property
    def average_ratings(self):
        result = self.product_reviews.aggregate(Avg("ratings"))
        return result["ratings__avg"] or 0

    @property
    def discount_price(self):
        if self.percentage_off > 0:
            discount = self.price - (self.price * self.percentage_off / 100)
            return discount
        return "Nil"


class ColourInventory(models.Model):
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="color_inventory"
    )
    colour = models.ForeignKey(
            Colour, on_delete=models.CASCADE, related_name="product_color"
    )
    quantity = models.IntegerField(default=0, blank=True)
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, blank=True, null=True
    )

    class Meta:
        verbose_name_plural = "Product Color & Inventories"

    def __str__(self):
        return self.product.title


class SizeInventory(models.Model):
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="size_inventory"
    )
    size = models.ForeignKey(
            Size, on_delete=models.CASCADE, related_name="product_size"
    )
    quantity = models.IntegerField(default=0, blank=True)
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, blank=True, null=True
    )

    class Meta:
        verbose_name_plural = "Product Size & Inventories"

    def __str__(self):
        return self.product.title


class ProductImage(models.Model):
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
            upload_to="store/images", validators=[validate_image_size]
    )

    def __str__(self):
        return self.product.title

    def image_url(self):
        try:
            url = self.image.url
        except:
            url = None
        return url


class FavoriteProduct(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, related_name="favorite_products"
    )
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="customer_favorites"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                    fields=["customer", "product"], name="unique_customer_product"
            )
        ]
        ordering = ('-created',)

    def __str__(self):
        return f"{self.customer.full_name} ----- {self.product.title}"


class SliderImage(BaseModel):
    image = models.ImageField(
            upload_to="slider_images/", validators=[validate_image_size]
    )

    class Meta:
        ordering = ('-created',)

    def image_url(self):
        try:
            url = self.image.url
        except:
            url = None
        return url


class ProductReview(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.DO_NOTHING, related_name="product_reviews"
    )
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="product_reviews"
    )
    ratings = models.IntegerField(choices=RATING_CHOICES, null=True)
    description = models.TextField()

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.customer.full_name} --- {self.product.title} --- {self.ratings} stars"


class ProductReviewImage(models.Model):
    product_review = models.ForeignKey(
            ProductReview, on_delete=models.CASCADE, related_name="product_review_images"
    )
    image = models.ImageField(
            upload_to="store/images", validators=[validate_image_size]
    )

    def image_url(self):
        try:
            url = self.image.url
        except:
            url = None
        return url


class Notification(BaseModel):
    customers = models.ManyToManyField(Customer)
    notification_type = models.CharField(max_length=1, choices=NOTIFICATION_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    general = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.notification_type} ---- {self.title}"


class CouponCode(BaseModel):
    code = models.CharField(max_length=8, unique=True, editable=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    expired = models.BooleanField(default=False)
    expiry_date = models.DateTimeField()  #

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = secrets.token_hex(4).upper()  # creates 8 letters

        if self.expiry_date and timezone.now() > self.expiry_date:
            self.expired = True
        super().save(*args, **kwargs)


class Order(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, related_name="orders")
    transaction_ref = models.UUIDField(default=uuid4, unique=True,
                                       editable=False)  # uuid is best for transaction references
    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
            max_length=1, choices=PAYMENT_STATUS, default=PAYMENT_PENDING
    )
    shipping_status = models.CharField(
            max_length=2, choices=SHIPPING_STATUS_CHOICES, default=SHIPPING_STATUS_PENDING
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f"{self.transaction_ref} --- {self.placed_at}"


class OrderItem(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="order_items", null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="orderitems"
    )
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    size = models.CharField(max_length=20, null=True)
    colour = models.CharField(max_length=20, null=True)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.order.transaction_ref} --- {self.product.title} --- {self.quantity}"
        )


class Cart(BaseModel):

    @cached_property
    def total_price(self):
        total_price = sum((item.product.price * item.product.quantity for item in self.items.all()))
        return total_price


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=20, null=True)
    colour = models.CharField(max_length=20, null=True)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                    fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"Cart id({self.cart.id}) ---- {self.product.title} ---- {self.quantity}"


class Country(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ('-created',)

    def __str__(self):
        return f"{self.name} -- {self.code}"


class Address(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, related_name="addresses"
    )
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255)
    second_street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ('-created',)

    def __str__(self):
        return f"{self.customer.full_name}"

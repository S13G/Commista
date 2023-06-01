import secrets

from autoslug import AutoSlugField
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from rest_framework.exceptions import ValidationError

from common.models import BaseModel
from core.validators import validate_phone_number
from store.choices import (CONDITION_CHOICES, GENDER_CHOICES, NOTIFICATION_CHOICES, PAYMENT_PENDING, PAYMENT_STATUS,
                           RATING_CHOICES, SHIPPING_STATUS_CHOICES, SHIPPING_STATUS_PENDING)
from store.managers import AddressManager, ColourInventoryManager, FavoriteProductManager, OrderItemManager, \
    OrderManager, \
    ProductManager, \
    ProductReviewManager, \
    SizeInventoryManager
from store.validators import validate_image_size

# Create your models here.

Customer = get_user_model()


class Category(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)

    class Meta:
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title


class Size(BaseModel):
    title = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.title


class Colour(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    hex_code = models.CharField(
            max_length=20, unique=True, help_text=_("Enter the hexadecimal code for the colour.")
    )

    def __str__(self):
        return f"{self.name} ---- {self.hex_code}"


class Product(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="title", unique=True, always_update=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    description = models.TextField()
    style = models.CharField(max_length=255, help_text=_("Enter the product style."))
    price = models.DecimalField(max_digits=6, decimal_places=2)
    shipped_out_days = models.IntegerField(default=settings.DEFAULT_PRODUCT_SHIPPING_DAYS)
    shipping_fee = models.DecimalField(
            max_digits=6, decimal_places=2, validators=[MinValueValidator(0)],
            default=settings.DEFAULT_PRODUCT_SHIPPING_FEE
    )
    inventory = models.IntegerField(
            validators=[MinValueValidator(0)], help_text=_("Product amount in stock.")
    )
    percentage_off = models.PositiveIntegerField(default=0)
    condition = models.CharField(
            max_length=2, choices=CONDITION_CHOICES, blank=True, null=True,
            help_text=_("Select the condition of the product.")
    )
    location = CountryField(help_text=_("Select the product's location"))
    flash_sale_start_date = models.DateTimeField(null=True, blank=True)
    flash_sale_end_date = models.DateTimeField(null=True, blank=True)

    objects = ProductManager()

    def __str__(self):
        return f"{self.title} --- {self.category}"

    @cached_property
    def average_ratings(self):
        # Calculate the average ratings for the product
        result = self.product_reviews.aggregate(Avg("ratings"))
        # Return the average ratings or 0 if no ratings are available
        return result["ratings__avg"] or 0

    @property
    def discount_price(self):
        # Check if a percentage discount is applicable
        if self.percentage_off > 0:
            # Calculate the discounted price based on the percentage off
            discount = self.price - (self.price * self.percentage_off / 100)
            return round(discount, 2)
        return 0


class ColourInventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="color_inventory")
    colour = models.ForeignKey(Colour, on_delete=models.CASCADE, related_name="product_color")
    quantity = models.IntegerField(
            default=0, blank=True, help_text=_("The quantity of this color variant in inventory.")
    )
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, blank=True, null=True, default=0,
            help_text=_("The extra price for this color variant.")
    )

    objects = ColourInventoryManager()

    class Meta:
        verbose_name_plural = _("Product Color & Inventories")

    def __str__(self):
        return self.product.title


class SizeInventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="size_inventory")
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name="product_size")
    quantity = models.IntegerField(
            default=0, blank=True, help_text=_("The quantity of this size variant in inventory.")
    )
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, blank=True, null=True, default=0,
            help_text=_("The extra price for this size variant.")
    )

    objects = SizeInventoryManager()

    class Meta:
        verbose_name_plural = _("Product Size & Inventories")

    def __str__(self):
        return self.product.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    _image = models.ImageField(upload_to='store/product_images', validators=[validate_image_size])

    def __str__(self):
        return self.product.title

    @property
    def image(self):
        if self._image is not None:
            return self._image.url
        return None


class FavoriteProduct(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="favorite_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="customer_favorites")

    objects = FavoriteProductManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                    fields=["customer", "product"], name="unique_customer_product"
            )
        ]

    def __str__(self):
        return f"{self.customer.full_name} ----- {self.product.title}"


class SliderImage(BaseModel):
    _image = models.ImageField(
            upload_to='store/slider_images/', validators=[validate_image_size],
            help_text=_("Image for the slider")
    )

    @property
    def slider_image(self):
        if self._image is not None:
            return self._image.url
        return None


class ProductReview(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, related_name="product_reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_reviews")
    ratings = models.IntegerField(choices=RATING_CHOICES, null=True)
    description = models.TextField()

    objects = ProductReviewManager()

    def __str__(self):
        return f"{self.customer.full_name} --- {self.product.title} --- {self.ratings} stars"


class ProductReviewImage(models.Model):
    product_review = models.ForeignKey(
            ProductReview, on_delete=models.CASCADE, related_name="images"
    )
    _image = models.ImageField(upload_to='store/review_images', validators=[validate_image_size])

    @property
    def review_image(self):
        if self._image is not None:
            return self._image.url
        return None


class Notification(BaseModel):
    customers = models.ManyToManyField(Customer, blank=True)
    notification_type = models.CharField(max_length=1, choices=NOTIFICATION_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    general = models.BooleanField(
            default=False, help_text=_("Whether the notification is general or specific to individual customers.")
    )

    def __str__(self):
        return f"{self.notification_type} ---- {self.title}"


class CouponCode(BaseModel):
    code = models.CharField(max_length=8, unique=True, editable=False)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    expired = models.BooleanField(default=False)
    expiry_date = models.DateTimeField()

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = secrets.token_hex(4).upper()  # creates 8 letters

        if self.expiry_date and (timezone.now() > self.expiry_date):
            self.expired = True

        # ensure expiry date is always in the future
        if self.expiry_date < timezone.now():
            raise ValidationError('Expiry date must be in the future.')
        super().save(*args, **kwargs)


class Order(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, related_name="orders")
    transaction_ref = models.CharField(max_length=32, unique=True, null=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(
            'Address', on_delete=models.SET_NULL, blank=True, null=True, related_name="orders_address"
    )
    payment_status = models.CharField(
            max_length=2, choices=PAYMENT_STATUS, default=PAYMENT_PENDING
    )
    shipping_status = models.CharField(
            max_length=2, choices=SHIPPING_STATUS_CHOICES, default=SHIPPING_STATUS_PENDING
    )

    objects = OrderManager()

    @property
    def all_total_price(self):
        cart_total = sum([item.total_price for item in self.order_items.all()])
        return cart_total

    @property
    def total_items(self):
        order_items = self.order_items.all()
        total = sum([item.quantity for item in order_items])
        return total

    @property
    def estimated_shipping_date(self):
        # adding on month to the date the order was placed
        return self.placed_at + relativedelta(months=settings.ORDER_SHIPPING_MONTHS)

    def __str__(self):
        return f"{self.transaction_ref} --- {self.placed_at}"


class OrderItem(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, related_name="order_items", null=True
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    extra_price = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    size = models.CharField(max_length=20, null=True)
    colour = models.CharField(max_length=20, null=True)
    ordered = models.BooleanField(default=False)

    objects = OrderItemManager()

    def __str__(self):
        return (
            f"{self.order.transaction_ref} --- {self.product.title} --- {self.quantity}"
        )

    @property
    def total_price(self):
        extra_price = self.extra_price
        if float(self.product.discount_price) > 0:
            return self.quantity * (self.product.discount_price + self.product.shipping_fee + extra_price)
        return self.quantity * (self.product.price + self.product.shipping_fee + extra_price)


class Address(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    country = CountryField()
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255)
    second_street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])

    objects = AddressManager()

    class Meta:
        verbose_name_plural = _("Addresses")

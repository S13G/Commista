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
from store.validators import validate_image_size

# Create your models here.

Customer = get_user_model()


class Category(BaseModel):
    title = models.CharField(
            max_length=255, unique=True, help_text=_("Enter the category title.")
    )
    gender = models.CharField(
            max_length=1, choices=GENDER_CHOICES, null=True,
            help_text=_("Select the gender for this category.")
    )

    class Meta:
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title


class Size(BaseModel):
    title = models.CharField(
            max_length=5, unique=True, help_text=_("Enter the size title.")
    )

    def __str__(self):
        return self.title


class Colour(BaseModel):
    name = models.CharField(
            max_length=20, unique=True, help_text=_("Enter the colour name.")
    )
    hex_code = models.CharField(
            max_length=20, unique=True, help_text=_("Enter the hexadecimal code for the colour.")
    )

    def __str__(self):
        return f"{self.name} ---- {self.hex_code}"


class ProductsManager(models.Manager):
    def get_queryset(self):
        return super(ProductsManager, self) \
            .get_queryset() \
            .prefetch_related(
                'category',
                'product_reviews',
                'size_inventory',
                'color_inventory',
                'images'
        ) \
            .filter(inventory__gt=0)


class Product(BaseModel):
    title = models.CharField(
            max_length=255, unique=True, help_text=_("Enter the product title.")
    )
    slug = AutoSlugField(
            populate_from="title", unique=True, always_update=True, editable=False,
            help_text=_("Auto-generated slug based on the product title.")
    )
    category = models.ForeignKey(
            Category, on_delete=models.CASCADE, related_name="products",
            help_text=_("Select the category for this product.")
    )
    description = models.TextField(
            help_text=_("Enter the product description.")
    )
    style = models.CharField(
            max_length=255, help_text=_("Enter the product style.")
    )
    price = models.DecimalField(
            max_digits=6, decimal_places=2, help_text=_("Enter the product price.")
    )
    shipped_out_days = models.IntegerField(
            help_text=_("Enter the number of days it takes to ship the product.")
    )
    shipping_fee = models.DecimalField(
            max_digits=6, decimal_places=2, validators=[MinValueValidator(0)],
            help_text=_("Enter the shipping fee for the product.")
    )
    inventory = models.IntegerField(
            validators=[MinValueValidator(0)], help_text=_("Enter the product inventory.")
    )
    percentage_off = models.PositiveIntegerField(
            default=0, help_text=_("Enter the percentage off for the product.")
    )
    condition = models.CharField(
            max_length=2, choices=CONDITION_CHOICES, blank=True, null=True,
            help_text=_("Select the condition of the product.")
    )
    location = CountryField(
            help_text=_("Select the location of the product.")
    )
    flash_sale_start_date = models.DateTimeField(
            null=True, blank=True, help_text=_("Enter the start date of the flash sale.")
    )
    flash_sale_end_date = models.DateTimeField(
            null=True, blank=True, help_text=_("Enter the end date of the flash sale.")
    )
    objects = models.Manager()
    categorized = ProductsManager()

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
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="color_inventory",
            help_text=_("The product associated with this color inventory.")
    )
    colour = models.ForeignKey(
            Colour, on_delete=models.CASCADE, related_name="product_color",
            help_text=_("The color associated with this product.")
    )
    quantity = models.IntegerField(
            default=0, blank=True, help_text=_("The quantity of this color variant in inventory.")
    )
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, blank=True, null=True, default=0,
            help_text=_("The extra price for this color variant.")
    )

    class Meta:
        verbose_name_plural = "Product Color & Inventories"

    def __str__(self):
        return self.product.title


class SizeInventory(models.Model):
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="size_inventory",
            help_text=_("The product associated with this size inventory.")
    )
    size = models.ForeignKey(
            Size, on_delete=models.CASCADE, related_name="product_size",
            help_text=_("The size associated with this product.")
    )
    quantity = models.IntegerField(
            default=0, blank=True, help_text=_("The quantity of this size variant in inventory.")
    )
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, blank=True, null=True, default=0,
            help_text=_("The extra price for this size variant.")
    )

    class Meta:
        verbose_name_plural = _("Product Size & Inventories")

    def __str__(self):
        return self.product.title


class ProductImage(models.Model):
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="images",
            help_text=_("The product associated with this image.")
    )
    _image = models.ImageField(
            upload_to='store/product_images', validators=[validate_image_size],
            help_text=_("The image of the product.")
    )

    def __str__(self):
        return self.product.title

    @property
    def image(self):
        if self._image is not None:
            return self._image.url
        return None


class FavoriteProduct(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, related_name="favorite_products",
            help_text=_("The customer who has marked this product as a favorite.")
    )
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="customer_favorites",
            help_text=_("The product marked as a favorite by the customer.")
    )

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
    customer = models.ForeignKey(
            Customer, on_delete=models.DO_NOTHING, related_name="product_reviews",
            help_text=_("The customer who wrote the review.")
    )
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="product_reviews",
            help_text=_("The product being reviewed.")
    )
    ratings = models.IntegerField(
            choices=RATING_CHOICES, null=True, help_text=_("The ratings given to the product.")
    )
    description = models.TextField(
            help_text=_("The description of the product review.")
    )

    def __str__(self):
        return f"{self.customer.full_name} --- {self.product.title} --- {self.ratings} stars"


class ProductReviewImage(models.Model):
    product_review = models.ForeignKey(
            ProductReview, on_delete=models.CASCADE, related_name="product_review_images",
            help_text=_("The product review associated with the image.")
    )
    _image = models.ImageField(
            upload_to='store/review_images', validators=[validate_image_size],
            help_text=_("Image for the product review.")
    )

    @property
    def review_image(self):
        if self._image is not None:
            return self._image.url
        return None


class Notification(BaseModel):
    customers = models.ManyToManyField(
            Customer, help_text=_("The customers associated with the notification.")
    )
    notification_type = models.CharField(
            max_length=1, choices=NOTIFICATION_CHOICES, help_text=_("The type of notification.")
    )
    title = models.CharField(
            max_length=255, help_text=_("The title of the notification.")
    )
    description = models.TextField(
            help_text=_("The description of the notification.")
    )
    general = models.BooleanField(
            default=False, help_text=_("Whether the notification is general or specific to individual customers.")
    )

    def __str__(self):
        return f"{self.notification_type} ---- {self.title}"


class CouponCode(BaseModel):
    code = models.CharField(
            max_length=8, unique=True, editable=False, help_text=_("The code for the coupon.")
    )
    price = models.DecimalField(
            max_digits=6, decimal_places=2, help_text=_("The price of the coupon.")
    )
    expired = models.BooleanField(
            default=False, help_text=_("Indicates whether the coupon is expired or not.")
    )
    expiry_date = models.DateTimeField(
            help_text=_("The date and time when the coupon expires.")
    )

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
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, null=True, related_name="orders",
            help_text=_("The customer who placed the order.")
    )
    transaction_ref = models.CharField(
            max_length=32, unique=True, help_text=_("The reference number for the transaction.")  #
    )
    placed_at = models.DateTimeField(
            auto_now_add=True, help_text=_("The date and time when the order was placed.")
    )
    total_price = models.DecimalField(
            max_digits=6, decimal_places=2, null=True, help_text=_("The total price of the order.")
    )
    address = models.ForeignKey(
            'Address', on_delete=models.SET_NULL, blank=True, null=True,
            related_name="orders_address", help_text=_("The address associated with the order.")
    )
    payment_status = models.CharField(
            max_length=2, choices=PAYMENT_STATUS, default=PAYMENT_PENDING,
            help_text=_("The payment status of the order.")
    )
    shipping_status = models.CharField(
            max_length=2, choices=SHIPPING_STATUS_CHOICES, default=SHIPPING_STATUS_PENDING,
            help_text=_("The shipping status of the order.")
    )

    @property
    def estimated_shipping_date(self):
        # adding on month to the date the order was placed
        return self.placed_at + relativedelta(months=settings.ORDER_SHIPPING_MONTHS)

    def __str__(self):
        return f"{self.transaction_ref} --- {self.placed_at}"


class OrderItem(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, related_name="order_items", null=True,
            help_text=_("The customer associated with the order item.")
    )
    order = models.ForeignKey(
            Order, on_delete=models.CASCADE, related_name="items",
            help_text=_("The order associated with the order item.")
    )
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, related_name="orderitems",
            help_text=_("The product associated with the order item.")
    )
    quantity = models.PositiveSmallIntegerField(
            validators=[MinValueValidator(1)], help_text=_("The quantity of the product in the order item.")
    )
    unit_price = models.DecimalField(
            max_digits=6, decimal_places=2, help_text=_("The unit price of the product in the order item.")
    )
    size = models.CharField(
            max_length=20, null=True, help_text=_("The size of the product in the order item.")
    )
    colour = models.CharField(
            max_length=20, null=True, help_text=_("The color of the product in the order item.")
    )
    ordered = models.BooleanField(
            default=False, help_text=_("Whether the order item has been ordered or not.")
    )

    def __str__(self):
        return (
            f"{self.order.transaction_ref} --- {self.product.title} --- {self.quantity}"
        )


class Cart(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, null=True, related_name="carts",
            help_text=_("The customer associated with the cart.")
    )


class CartItem(BaseModel):
    cart = models.ForeignKey(
            Cart, on_delete=models.CASCADE, related_name="items",
            help_text=_("The cart associated with the cart item.")
    )
    product = models.ForeignKey(
            Product, on_delete=models.CASCADE, help_text=_("The product associated with the cart item.")
    )
    size = models.CharField(
            max_length=20, null=True, help_text=_("The size of the product in the cart item.")
    )
    colour = models.CharField(
            max_length=20, null=True, help_text=_("The color of the product in the cart item.")
    )
    quantity = models.PositiveSmallIntegerField(
            validators=[MinValueValidator(1)], help_text=_("The quantity of the product in the cart item.")
    )
    extra_price = models.DecimalField(
            max_digits=6, decimal_places=2, null=True,
            help_text=_("Any additional price associated with the cart item.")
    )


class Address(BaseModel):
    customer = models.ForeignKey(
            Customer, on_delete=models.CASCADE, related_name="addresses",
            help_text=_("The customer associated with the address."))
    country = CountryField(
            help_text=_("The country of the address.")
    )
    first_name = models.CharField(
            max_length=255, help_text=_("The first name associated with the address.")
    )
    last_name = models.CharField(
            max_length=255, help_text=_("The last name associated with the address.")
    )
    street_address = models.CharField(
            max_length=255, help_text=_("The street address of the address.")
    )
    second_street_address = models.CharField(
            max_length=255, blank=True, null=True, help_text=_("The second street address of the address.")
    )
    city = models.CharField(
            max_length=255, help_text=_("The city of the address.")
    )
    state = models.CharField(
            max_length=255, help_text=_("The state of the address.")
    )
    zip_code = models.CharField(
            max_length=10, help_text=_("The ZIP code of the address.")
    )
    phone_number = models.CharField(
            max_length=20, validators=[validate_phone_number],
            help_text=_("The phone number associated with the address.")
    )

    class Meta:
        verbose_name_plural = _("Addresses")

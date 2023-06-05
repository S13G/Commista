import uuid
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django_countries.fields import CountryField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from store.choices import PAYMENT_STATUS, RATING_CHOICES, SHIPPING_STATUS_CHOICES
from store.models import Address, Colour, ColourInventory, CouponCode, Order, OrderItem, Product, \
    ProductImage, Size, SizeInventory


class AddCheckoutOrderAddressSerializer(serializers.Serializer):
    tx_ref = serializers.CharField()
    address_id = serializers.UUIDField()

    def validate(self, attrs):
        customer = self.context['request'].user
        tx_ref = attrs.get('tx_ref')
        address_id = attrs.get('address_id')

        try:
            Order.objects.get(customer=customer, transaction_ref=tx_ref)
        except Order.DoesNotExist:
            raise serializers.ValidationError(
                    {"message": f"Customer does not have an order with this transaction reference: {tx_ref}",
                     "status": "failed"})

        try:
            Address.objects.get(customer=customer, id=address_id)
        except Address.DoesNotExist:
            raise serializers.ValidationError(
                    {"message": f"Customer does not have an address with this id: {address_id}", "status": "failed"})

        return attrs

    def save(self, **kwargs):
        customer = self.context['request'].user
        tx_ref = self.validated_data['tx_ref']
        address_id = self.validated_data['address_id']

        # Check if the address is already added to the order
        try:
            order = Order.objects.get(customer=customer, transaction_ref=tx_ref)
            if order.address_id == address_id:
                return ValidationError({"message": "This address is already added to the order.", "status": "failed"})
        except Order.DoesNotExist:
            return ValidationError(
                    {"message": "Customer does not have an order with this transaction reference.", "status": "failed"})
        address = Address.objects.get(customer=customer, id=address_id)

        order.address = address
        order.save()

        return order


class ColourSerializer(serializers.Serializer):
    name = serializers.CharField()
    hex_code = serializers.CharField()

    class Meta:
        model = Colour


class ColourInventorySerializer(serializers.Serializer):
    colour = ColourSerializer()
    quantity = serializers.IntegerField()
    extra_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        model = ColourInventory


class SizeSerializer(serializers.Serializer):
    title = serializers.CharField()

    class Meta:
        model = Size


class SizeInventorySerializer(serializers.Serializer):
    size = SizeSerializer()
    quantity = serializers.IntegerField()
    extra_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        model = SizeInventory


class ProductImageSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    _image = serializers.ImageField()

    class Meta:
        model = ProductImage

    def validate__image(self, attrs):
        image = attrs.get('_image')
        max_size = 3 * 1024 * 1024  # 3MB in bytes
        if image.size > max_size:
            raise ValidationError({"message": f"Image {image} size should be less than 3MB", "status": "failed"})
        return attrs


class SimpleProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    images = ProductImageSerializer(many=True)

    class Meta:
        model = Product


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.SlugField()
    category = serializers.CharField(source="category.title")
    description = serializers.CharField()
    style = serializers.CharField()
    price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage_off = serializers.IntegerField()
    discount_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    images = serializers.SerializerMethodField()
    sizes = SizeInventorySerializer(many=True, read_only=True)
    colours = ColourInventorySerializer(many=True, read_only=True)
    shipped_out_days = serializers.IntegerField()

    class Meta:
        model = Product

    def get_images(self, obj: Product):
        return [image.image for image in obj.images.all()]


class ProductDetailSerializer(ProductSerializer):
    inventory = serializers.IntegerField()
    condition = serializers.CharField()
    shipping_fee = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    location = serializers.CharField()
    average_ratings = serializers.DecimalField(max_digits=4, decimal_places=2, default=0)


class FavoriteProductSerializer(serializers.Serializer):
    product = ProductSerializer()
    sizes = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()


class ProductReviewSerializer(serializers.Serializer):
    customer_name = serializers.CharField(source="customer.full_name")
    ratings = serializers.ChoiceField(choices=RATING_CHOICES)
    description = serializers.CharField()


class AddProductReviewSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    ratings = serializers.ChoiceField(choices=RATING_CHOICES)
    description = serializers.CharField()
    images = serializers.ListField(
            child=serializers.ImageField(), required=False, max_length=3
    )

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise ValidationError(
                    {
                        "message": "This product does not exist, try again",
                        "status": "failed",
                    }
            )
        return value


class CartItemSerializer(serializers.Serializer):
    product = SimpleProductSerializer()
    cart_id = serializers.UUIDField(source="order_id")
    discount_price = serializers.DecimalField(
            max_digits=6, decimal_places=2, source="product.discount_price"
    )
    size = serializers.CharField()
    colour = serializers.CharField()
    extra_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)
    quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=6, decimal_places=2, default=0)


def validate_cart_item(attrs):
    product_id = attrs.get("product_id")
    if not Product.objects.filter(id=product_id).exists():
        raise ValidationError(
                {"message": "No product with the given ID was found.", "status": "failed"}
        )

    product = Product.objects.get(id=product_id)

    size = attrs.get("size")
    if size and not product.size_inventory.filter(size__title=size).exists():
        raise ValidationError(
                {"message": "Size not found for the given product.", "status": "failed"}
        )

    colour = attrs.get("colour")
    if colour and not product.color_inventory.filter(colour__name=colour).exists():
        raise ValidationError(
                {"message": "Colour not found for the given product.", "status": "failed"}
        )

    return attrs


class AddCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=False, default=None, allow_blank=True)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False, allow_blank=True)
    colour = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField()

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        customer = self.context["request"].user
        product_id = self.validated_data["product_id"]
        size = self.validated_data.get("size")
        colour = self.validated_data.get("colour")
        quantity = self.validated_data["quantity"]
        cart_id = self.validated_data.get("cart_id", str(uuid.uuid4()))

        product = get_object_or_404(Product, id=product_id)
        if product.inventory <= 0:
            raise ValidationError({"message": "This product is out of stock", "status": "failed"})
        cart, _ = Order.objects.get_or_create(id=cart_id, customer=customer)

        extra_price = 0
        if size:
            size_inv = get_object_or_404(SizeInventory, size__title__iexact=size, product=product)
            if size_inv.quantity <= 0:
                raise ValidationError({"message": "Size for this product is out of stock", "status": "failed"})
            extra_price += size_inv.extra_price

        if colour:
            colour_inv = get_object_or_404(ColourInventory, colour__name__iexact=colour, product=product)
            if colour_inv.quantity <= 0:
                raise ValidationError({"message": "Colour for this product is out of stock", "status": "failed"})
            extra_price += colour_inv.extra_price

        cart_item = cart.order_items.filter(product=product, size=size, colour=colour).first()

        if cart_item:
            cart_item.quantity = quantity
            cart_item.extra_price = extra_price
            cart_item.save()
        else:
            cart_item = OrderItem.objects.create(
                    customer=customer,
                    order=cart,
                    product=product,
                    size=size,
                    colour=colour,
                    quantity=quantity,
                    extra_price=extra_price
            )

        if cart_item.quantity == 0:
            cart_item.delete()

        if cart.order_items.count() == 0:
            cart.delete()

        return cart_item


class UpdateCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False, allow_blank=True)
    colour = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        customer = self.context["request"].user
        cart_id = self.validated_data["cart_id"]
        product_id = self.validated_data["product_id"]
        size = self.validated_data.get("size", "")
        colour = self.validated_data.get("colour", "")

        try:
            cart = Order.objects.get(id=cart_id, customer=customer)
            product = Product.objects.get(id=product_id)
            item = OrderItem.objects.get(order=cart, product=product)
        except Order.DoesNotExist:
            raise ValidationError({
                "message": "Invalid cart ID. Please check the provided ID.",
                "status": "failed",
            })
        except Product.DoesNotExist:
            raise ValidationError({
                "message": "Invalid product ID. Please check the provided ID.",
                "status": "failed",
            })
        except OrderItem.DoesNotExist:
            raise ValidationError({
                "message": "Cart item does not exist. Please add the product to the cart first.",
                "status": "failed",
            })

        if size:
            item.size = size

        if colour:
            item.colour = colour

        item.extra_price = self.determine_extra_price(item)
        item.save()

        return item

    @staticmethod
    def determine_extra_price(cart_item):
        total_extra_price = 0

        if cart_item.colour:
            try:
                colour_obj = ColourInventory.objects.get(
                        colour__name__iexact=cart_item.colour, product=cart_item.product
                )
                total_extra_price += colour_obj.extra_price
            except ColourInventory.DoesNotExist:
                pass

        if cart_item.size:
            try:
                size_obj = SizeInventory.objects.get(
                        size__title__iexact=cart_item.size, product=cart_item.product
                )
                total_extra_price += size_obj.extra_price
            except SizeInventory.DoesNotExist:
                pass

        return total_extra_price


class DeleteCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=True)
    product_id = serializers.CharField(max_length=100, required=True)

    def save(self, **kwargs):
        customer = self.context["request"].user
        try:
            cart = Order.objects.get(id=self.validated_data["cart_id"], customer=customer)
            product = Product.objects.get(id=self.validated_data.get("product_id"))
            item = OrderItem.objects.get(order=cart, product=product)
        except (Order.DoesNotExist, Product.DoesNotExist, OrderItem.DoesNotExist):
            raise ValidationError(
                    {
                        "message": "Invalid cart or product ID. Please check the provided IDs.",
                        "status": "failed",
                    }
            )
        item.delete()


class OrderSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    transaction_ref = serializers.CharField()
    items = serializers.SerializerMethodField()
    all_total_price = serializers.DecimalField(max_digits=6, decimal_places=2)
    placed_at = serializers.DateTimeField()
    address = serializers.UUIDField(allow_null=True)
    estimated_shipping_date = serializers.DateTimeField()
    shipping_status = serializers.ChoiceField(choices=SHIPPING_STATUS_CHOICES)
    payment_status = serializers.ChoiceField(choices=PAYMENT_STATUS)

    def get_items(self, obj: Order):
        return [
            {
                "customer": item.customer.full_name,
                "title": item.product.title,
                "price": item.product.price,
                "shipping_fee": item.product.shipping_fee,
                "shipping_out_date": (obj.placed_at + timedelta(days=item.product.shipped_out_days)),
                "quantity": item.quantity,
                "size": item.size,
                "colour": item.colour
            }
            for item in obj.order_items.all()
        ]


class OrderListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    transaction_ref = serializers.CharField()
    items_count = serializers.SerializerMethodField()
    all_total_price = serializers.DecimalField(max_digits=6, decimal_places=2)
    placed_at = serializers.DateTimeField()
    address = serializers.UUIDField(allow_null=True)
    estimated_shipping_date = serializers.DateTimeField()
    shipping_status = serializers.ChoiceField(choices=SHIPPING_STATUS_CHOICES)
    payment_status = serializers.ChoiceField(choices=PAYMENT_STATUS)

    @staticmethod
    def get_items_count(obj: Order):
        return f"{obj.order_items.count()} item(s) ordered"


class CheckoutSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def save(self, **kwargs):
        customer = self.context["request"].user
        coupon_discount = 0

        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().filter(customer=customer).first()
            except Order.DoesNotExist:
                raise ValidationError({"message": "Cart not found", "status": "failed"})

            if self.validated_data.get("coupon_code"):
                try:
                    coupon = CouponCode.objects.get(
                            code=self.validated_data["coupon_code"], expired=False
                    )
                    coupon_discount = coupon.price
                    coupon.expired = True
                    coupon.save()
                except CouponCode.DoesNotExist:
                    raise ValidationError(
                            {"message": "Invalid coupon code", "status": "failed"}
                    )

            transaction_ref = uuid.uuid4().hex[:10]
            if order.transaction_ref:
                raise ValidationError(
                        {"message": "Order has already been checked out. Make a different order", "status": "failed"})

            order.transaction_ref = f"TR-{transaction_ref}"
            order.all_total_price - coupon_discount
            order.save()

        return order

    def to_representation(self, instance: Order):
        items = instance.order_items.values_list(
                "id", "product__id", "product__title", "quantity", "product__shipping_fee", "product__shipped_out_days"
        )
        return {
            "id": instance.id,
            "customer": instance.customer.full_name,
            "transaction_reference": instance.transaction_ref,
            "total_price": instance.all_total_price,
            "placed_at": instance.placed_at,
            "address": instance.address,
            "estimated_shipping_date": instance.estimated_shipping_date,
            "shipping_status": instance.shipping_status,
            "payment_status": instance.payment_status,
            "items": [
                {
                    "id": item[0],
                    "product_id": item[1],
                    "product__title": item[2],
                    "quantity": item[3],
                    "shipping_fee": item[4],
                    "shipped_out_days": item[5]
                }
                for item in items
            ],
        }


class AddressSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    street_address = serializers.CharField(max_length=255)
    second_street_address = serializers.CharField(max_length=255, allow_blank=True)
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        phone_number = value
        if not phone_number.startswith('+'):
            raise ValidationError("Phone number must start with a plus sign (+)")
        if not phone_number[1:].isdigit():
            raise ValidationError("Phone number must only contain digits after the plus sign (+)")
        return value


class CreateAddressSerializer(AddressSerializer):
    id = serializers.UUIDField(allow_null=True, required=False)
    country = CountryField()
    second_street_address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=255)
    zip_code = serializers.CharField(max_length=10)

    def validate_zip_code(self, value):
        zip_code = value
        if not zip_code.isdigit() or len(zip_code) > 6:
            raise serializers.ValidationError({"message": "Invalid zip code.", "status": "failed"})
        return value

    def create(self, validated_data):
        customer = self.context['request'].user
        address = Address.objects.create(customer=customer, **validated_data)
        return address

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

import uuid
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from store.models import Address, Colour, ColourInventory, CouponCode, FavoriteProduct, Order, OrderItem, Product, \
    ProductImage, ProductReview, Size, SizeInventory


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
                    f"Customer does not have an order with this transaction reference: {tx_ref}")

        try:
            Address.objects.get(customer=customer, id=address_id)
        except Address.DoesNotExist:
            raise serializers.ValidationError(f"Customer does not have an address with this id: {address_id}")

        return attrs

    def save(self, **kwargs):
        customer = self.context['request'].user
        tx_ref = self.validated_data['tx_ref']
        address_id = self.validated_data['address_id']

        # Check if the address is already added to the order
        try:
            order = Order.objects.get(customer=customer, transaction_ref=tx_ref)
            if order.address_id == address_id:
                return ValidationError({"message": "This address is already added to the order."})
        except Order.DoesNotExist:
            return ValidationError({"message": "Customer does not have an order with this transaction reference."})
        address = Address.objects.get(customer=customer, id=address_id)

        order.address = address
        order.save()

        return order


class ColourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colour
        fields = ["name", "hex_code"]


class ColourInventorySerializer(serializers.ModelSerializer):
    colour = ColourSerializer()

    class Meta:
        model = ColourInventory
        fields = ["colour", "quantity", "extra_price"]


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ["title"]


class SizeInventorySerializer(serializers.ModelSerializer):
    size = SizeSerializer()

    class Meta:
        model = SizeInventory
        fields = ["size", "quantity", "extra_price"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class SimpleProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)

    class Meta:
        model = Product
        fields = ["id", "title", "price", "images"]


class ProductSerializer(serializers.ModelSerializer):
    sizes = SizeInventorySerializer(source="size_inventory", many=True, read_only=True)
    colours = ColourInventorySerializer(
            source="color_inventory", many=True, read_only=True
    )
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "description",
            "style",
            "price",
            "percentage_off",
            "images",
            "colours",
            "sizes",
        ]

    @staticmethod
    def get_images(obj: Product):
        return [image.image for image in obj.images.all()]


class ProductDetailSerializer(ProductSerializer):
    class Meta:
        model = Product
        fields = ProductSerializer.Meta.fields + [
            "inventory",
            "condition",
            "shipping_fee",
            "location",
            "discount_price",
            "average_ratings",
        ]


class FavoriteProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    flash_sale_start_date = serializers.DateTimeField(
            source="product.flash_sale_start_date"
    )
    flash_sale_end_date = serializers.DateTimeField(
            source="product.flash_sale_end_date"
    )
    condition = serializers.CharField(source="product.condition")
    location = serializers.CharField(source="product.location")
    discount_price = serializers.DecimalField(
            max_digits=6, decimal_places=2, source="product.discount_price"
    )
    average_ratings = serializers.IntegerField(source="product.average_ratings")

    class Meta:
        model = FavoriteProduct
        fields = [
            "id",
            "product",
            "flash_sale_start_date",
            "flash_sale_end_date",
            "condition",
            "location",
            "discount_price",
            "average_ratings",
        ]

    @staticmethod
    def get_size(obj):
        return [size.title for size in obj.product.size_inventory.all()]

    @staticmethod
    def get_color(obj):
        return [color.name for color in obj.product.color_inventory.all()]

    @staticmethod
    def get_images(obj):
        return [image.image for image in obj.product.images.all()]


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name")

    class Meta:
        model = ProductReview
        fields = ("customer_full_name", "ratings", "description")


class AddProductReviewSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField()
    images = serializers.ListField(
            child=serializers.ImageField(), required=False, max_length=3
    )

    class Meta:
        model = ProductReview
        fields = ["product_id", "ratings", "description", "images"]

    @staticmethod
    def validate_product_id(value):
        if not Product.categorized.filter(id=value).exists():
            raise ValidationError(
                    {
                        "message": "This product does not exist, try again",
                        "status": "failed",
                    }
            )
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    discount_price = serializers.DecimalField(
            max_digits=6, decimal_places=2, source="product.discount_price"
    )

    class Meta:
        model = OrderItem
        fields = ["order_id", "product", "size", "colour", "quantity", "discount_price", "quantity", "total_price"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer()

    class Meta:
        model = Order
        fields = ["id", "order_items", "total_price", "total_items"]


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
            cart_item = [
                OrderItem(
                        customer=customer,
                        order=cart,
                        product=item.product,
                        size=item.size,
                        colour=item.colour,
                        quantity=item.quantity,
                        extra_price=item.extra_price
                )
                for item in cart.order_items.all()
            ]
            OrderItem.objects.bulk_create(cart_item)

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


class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'transaction_ref', 'items', 'total_price', 'placed_at', 'estimated_shipping_date',
                  'shipping_status', 'payment_status']

    @staticmethod
    def get_items(obj: Order):
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


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'transaction_ref', 'items_count', 'total_price', 'placed_at', 'estimated_shipping_date',
                  'payment_status']

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
                cart = Order.objects.select_for_update().get(customer=customer)
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

            cart.transaction_ref = f"TR-{transaction_ref}"
            cart.total_price -= coupon_discount
            order = cart.save()

        return order

    def to_representation(self, instance: Order):
        items = instance.order_items.values_list(
                "id", "product__id", "product__title", "quantity", "product__shipping_fee"
        )
        return {
            "id": instance.id,
            "customer": instance.customer.full_name,
            'transaction_reference"': instance.transaction_ref,
            "total_price": instance.total_price,
            "placed_at": instance.placed_at,
            "estimated_shipping_date": instance.estimated_shipping_date,
            "shipping_status": instance.shipping_status,
            "payment_status": instance.payment_status,
            "items": [
                {
                    "id": item[0],
                    "product_id": item[1],
                    "product__title": item[2],
                    "quantity": item[3],
                    "shipping_fee": item[4]
                }
                for item in items
            ],
        }


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'first_name', 'last_name', 'street_address', 'second_street_address', 'phone_number']


class CreateAddressSerializer(serializers.ModelSerializer):
    second_street_address = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Address
        fields = ['country', 'first_name', 'last_name', 'street_address', 'second_street_address', 'city', 'state',
                  'zip_code', 'phone_number']

    def create(self, validated_data):
        customer = self.context['request'].user
        address = Address.objects.create(customer=customer, **validated_data)
        return address

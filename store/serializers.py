import uuid
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from store.models import Cart, CartItem, Colour, ColourInventory, CouponCode, FavoriteProduct, Order, OrderItem, \
    Product, ProductImage, ProductReview, \
    Size, SizeInventory


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
    images = ProductImageSerializer(many = True)
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
    images = serializers.ListField(
        child=serializers.ImageField(), required=False, max_length=3
    )

    class Meta:
        model = ProductReview
        fields = ["id", "ratings", "description", "images"]

    @staticmethod
    def validate_id(value):
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
    # total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["cart_id", "product","size","colour","quantity", "discount_price", "quantity", "total_price"]

    

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     request_data = self.context["request"].data
    #     colour = request_data.get("colour")
    #     size = request_data.get("size")
    #     # Filter the colours list to only include the specified colour
    #     if colour:
    #         colours = [
    #             c
    #             for c in ret["product"]["colours"]
    #             if c["colour"]["name"].lower() == colour.lower()
    #         ]
    #         ret["product"]["colours"] = [
    #             {
    #                 "colour": {
    #                     "name": c["colour"]["name"],
    #                     "hex_code": c["colour"]["hex_code"],
    #                 },
    #                 "extra_price": c["extra_price"],
    #             }
    #             for c in colours
    #         ]
    #     # Filter the sizes list to only include the specified colour
    #     if size:
    #         sizes = [
    #             c
    #             for c in ret["product"]["sizes"]
    #             if c["size"]["title"].lower() == size.lower()
    #         ]
    #         ret["product"]["sizes"] = [
    #             {"size": {"name": c["size"]["title"]}, "extra_price": c["extra_price"]}
    #             for c in sizes
    #         ]

    #     return ret


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]


def validate_cart_item(attrs):
    product_id = attrs["product_id"]
    if not Product.objects.filter(id=product_id).exists():
        raise serializers.ValidationError(
            {"message": "No product with the given ID was found.", "status": "failed"}
        )

    product = Product.objects.get(id=product_id)
    size = attrs.get("size")
    if size and not product.size_inventory.filter(size__title=size).exists():
        raise serializers.ValidationError(
            {"message": "Size not found for the given product.", "status": "failed"}
        )

    colour = attrs.get("colour")
    if colour and not product.color_inventory.filter(colour__name=colour).exists():
        raise serializers.ValidationError(
            {"message": "Colour not found for the given product.", "status": "failed"}
        )

    return attrs


class AddCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(
        max_length=60, required=False, default=None, allow_blank=True
    )
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False, allow_blank=True)
    colour = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField()

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        product = Product.objects.get(id=self.validated_data.get("product_id"))
        cart_id = self.validated_data.get("cart_id")
        size = self.validated_data.get("size")
        colour = self.validated_data.get("colour")
        quantity = self.validated_data.get("quantity")
        customer = self.context["request"].user

        if not cart_id:
            # create a random UUID because the Cart will attempt to compare UUID to an empty-string and will result in runtime error
            cart_id = uuid.uuid4()

        cart, _ = Cart.objects.get_or_create(id=cart_id, customer=customer)

        cart_item_obj = CartItem.objects.filter(cart=cart, product=product)
        # Get the extra price of the selected colour and size
        # And filter the Cart_Item queryset depending on the input
        extra_price = 0
        if size:
            size_inv_obj = SizeInventory.objects.get(
                size__title__iexact=size, product=product
            )
            extra_price += size_inv_obj.extra_price
            cart_item_obj = cart_item_obj.filter(size=size)
        if colour:
            colour_inv_obj = ColourInventory.objects.get(
                colour__name__iexact=colour, product=product
            )
            extra_price += colour_inv_obj.extra_price
            cart_item_obj = cart_item_obj.filter(colour=colour)

        if all([size, colour]):
            cart_item_obj = cart_item_obj.filter(colour=colour, size=size)

        try:
            item = cart_item_obj.get()
            item.quantity += quantity
            item.extra_price = extra_price
            item.save()
        except CartItem.DoesNotExist:
            item = CartItem.objects.create(
                cart=cart,
                product=product,
                size=size,
                colour=colour,
                quantity=quantity,
                extra_price=extra_price,
            )

        if item.quantity == 0:
            item.delete()

        if cart.items.count() == 0:
            cart.delete()
        return item

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     product_serializer = ProductSerializer(instance.product)
    #
    #     # Only include the color or size that was added to the cart
    #     if 'color' in ret:
    #         ret['color'] = ColourSerializer(instance.color).data
    #     if 'size' in ret:
    #         ret['size'] = SizeSerializer(instance.size).data
    #
    #     ret['product'] = product_serializer.data
    #     return ret


class UpdateCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, default=None)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False, allow_blank=True)
    colour = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        try:
            cart = Cart.objects.get(id=self.validated_data.get("cart_id"))
            product = Product.objects.get(id=self.validated_data.get("product_id"))
            item = CartItem.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, Product.DoesNotExist, CartItem.DoesNotExist):
            raise serializers.ValidationError(
                {
                    "message": "Invalid cart or product ID. Please check the provided IDs.",
                    "status": "failed",
                }
            )
        if self.validated_data.get("size"):
            item.size = self.validated_data["size"]
        if self.validated_data.get("colour"):
            item.colour = self.validated_data["colour"]
        item.save()
        return item


class DeleteCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=True)
    product_id = serializers.CharField(max_length=100, required=True)

    def save(self, **kwargs):
        try:
            cart = Cart.objects.get(id=self.validated_data["cart_id"])
            product = Product.objects.get(id=self.validated_data.get("product_id"))
            item = CartItem.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, Product.DoesNotExist, CartItem.DoesNotExist):
            raise serializers.ValidationError(
                {
                    "message": "Invalid cart or product ID. Please check the provided IDs.",
                    "status": "failed",
                }
            )
        item.delete()


class CreateOrderSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def save(self, **kwargs):
        customer = self.context["request"].user
        print(customer)
        coupon_code = self.validated_data.get("coupon_code", "")
        try:
            cart = Cart.objects.select_for_update().filter(customer=customer)
            print(cart)
        except Cart.DoesNotExist:
            raise ValidationError({"message": "Cart not found", "status": "failed"})

        with transaction.atomic():
            coupon_discount = None
            try:
                coupon = CouponCode.objects.get(code=coupon_code, expired=False)
                coupon_discount = coupon.price
            except CouponCode.DoesNotExist:
                raise ValidationError(
                    {"message": "Invalid coupon code", "status": "failed"}
                )

            order = Order.objects.create(
                customer=customer, total_price=cart.total_price - (coupon_discount or 0)
            )
            order.transaction_ref = f"TR-{order.transaction_ref}"

            for item in cart.items.all():
                OrderItem.objects.create(
                    customer=customer,
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    size=item.size,
                    colour=item.colour,
                )
            cart.delete()
        return order

    def to_representation(self, instance: Order):
        items = instance.items.values_list(
            "id", "product__id", "product__title", "quantity"
        )
        return {
            "id": instance.id,
            "customer": instance.customer.full_name,
            'transaction_reference"': instance.transaction_ref,
            "total_price": instance.total_price,
            "placed_at": instance.placed_at,
            "shipping_status": instance.shipping_status,
            "payment_status": instance.payment_status,
            "items": [
                {
                    "id": item[0],
                    "product_id": item[1],
                    "product__title": item[2],
                    "quantity": item[3],
                }
                for item in items
            ],
        }

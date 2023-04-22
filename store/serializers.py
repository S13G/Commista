from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from store.models import Cart, CartItem, Colour, ColourInventory, CouponCode, FavoriteProduct, Order, OrderItem, \
    Product, ProductReview, \
    Size, SizeInventory


class ColourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colour
        fields = ['name', 'hex_code']


class ColourInventorySerializer(serializers.ModelSerializer):
    colour = ColourSerializer()

    class Meta:
        model = ColourInventory
        fields = ['colour', 'quantity', 'extra_price']


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['title']


class SizeInventorySerializer(serializers.ModelSerializer):
    size = SizeSerializer()

    class Meta:
        model = SizeInventory
        fields = ['size', 'quantity', 'extra_price']


class ProductSerializer(serializers.ModelSerializer):
    sizes = SizeInventorySerializer(source='size_inventory', many=True, read_only=True)
    colours = ColourInventorySerializer(source='colour_inventory', many=True, read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'description', 'style', 'price', 'percentage_off', 'images',
                  'colours', 'sizes']

    @staticmethod
    def get_images(obj: Product):
        return [image.image for image in obj.images.all()]


class ProductDetailSerializer(ProductSerializer):
    class Meta:
        model = Product
        fields = ProductSerializer.Meta.fields + ['inventory', 'condition', 'location', 'discount_price',
                                                  'average_ratings']


class FavoriteProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    flash_sale_start_date = serializers.DateTimeField(source='product.flash_sale_start_date')
    flash_sale_end_date = serializers.DateTimeField(source='product.flash_sale_end_date')
    condition = serializers.CharField(source='product.condition')
    location = serializers.CharField(source='product.location')
    discount_price = serializers.DecimalField(max_digits=6, decimal_places=2, source='product.discount_price')
    average_ratings = serializers.IntegerField(source='product.average_ratings')


    class Meta:
        model = FavoriteProduct
        fields = ['id', 'product', 'flash_sale_start_date', 'flash_sale_end_date', 'condition', 'location',
                  'discount_price', 'average_ratings']

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
    customer_name = serializers.CharField(source='customer.full_name')

    class Meta:
        model = ProductReview
        fields = ('customer_full_name', 'ratings', 'description')


class AddProductReviewSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False, max_length=3)

    class Meta:
        model = ProductReview
        fields = ['id', 'ratings', 'description', 'images']

    @staticmethod
    def validate_id(value):
        if not Product.categorized.filter(id=value).exists():
            raise ValidationError({"message": "This product does not exist, try again", "status": "failed"})
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['cart_id', 'product', 'quantity', 'total_price']

    @staticmethod
    def get_total_price(cartitem: CartItem):
        if cartitem.product.discount_price > 0:
            return cartitem.quantity * cartitem.product.discount_price
        return cartitem.quantity * cartitem.product.price


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']


def validate_cart_item(attrs):
    product_id = attrs['product_id']
    if not Product.objects.filter(id=product_id).exists():
        raise serializers.ValidationError({"message": "No product with the given ID was found.", "status": "failed"})

    product = Product.objects.get()
    size = attrs.get('size')
    if size and not product.size.filter(title=size).exists():
        raise serializers.ValidationError({"message": "Size not found for the given product.", "status": "failed"})

    colour = attrs.get('colour')
    if colour and not product.colour.filter(name=colour).exists():
        raise serializers.ValidationError({"message": "Colour not found for the given product.", "status": "failed"})

    return attrs


class AddCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=False, default=None)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False, allow_blank=True)
    colour = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField()

    def validate(self, attrs):
        attrs = validate_cart_item(attrs)
        return attrs

    def save(self, **kwargs):
        product = Product.objects.get()
        cart_id = self.validated_data.get('cart_id')
        size = self.validated_data.get('size')
        colour = self.validated_data.get('colour')
        quantity = self.validated_data.get('quantity')

        if cart_id is None:
            cart = Cart.objects.get_or_create(defaults={})
        else:
            cart, _ = Cart.objects.get_or_create(id=cart_id)

        try:
            item = CartItem.objects.get(cart=cart, product=product, size=size, colour=colour)
            item.quantity += quantity
            item.save()
        except CartItem.DoesNotExist:
            item = CartItem.objects.create(cart=cart, product=product, size=size, colour=colour, quantity=quantity)
        if item.quantity == 0:
            item.delete()

        if cart.items.count() == 0:
            cart.delete()
        return item


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
            cart = Cart.objects.get(id=self.validated_data['cart_id'])
            product = Product.objects.get()
            item = CartItem.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, Product.DoesNotExist, CartItem.DoesNotExist):
            raise serializers.ValidationError(
                    {"message": "Invalid cart or product ID. Please check the provided IDs.", "status": "failed"})
        if self.validated_data.get('size'):
            item.size = self.validated_data['size']
        if self.validated_data.get('colour'):
            item.colour = self.validated_data['colour']
        item.save()
        return item


class DeleteCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=True)
    product_id = serializers.CharField(max_length=100, required=True)

    def save(self, **kwargs):
        try:
            cart = Cart.objects.get(id=self.validated_data['cart_id'])
            product = Product.objects.get()
            item = CartItem.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, Product.DoesNotExist, CartItem.DoesNotExist):
            raise serializers.ValidationError(
                    {"message": "Invalid cart or product ID. Please check the provided IDs.", "status": "failed"})
        item.delete()


class CreateOrderSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def save(self, **kwargs):
        customer = self.context['request'].user
        coupon_code = self.validated_data.get('coupon_code', '')
        try:
            cart = Cart.objects.select_for_update().get(customer=customer)
        except Cart.DoesNotExist:
            raise ValidationError({"message": "Cart not found", "status": "failed"})


        with transaction.atomic():
            try:
                coupon = CouponCode.objects.get(code=coupon_code, expired=False)
                coupon_discount = coupon.price
            except CouponCode.DoesNotExist:
                raise ValidationError({"message": "Invalid coupon code", "status": "failed"})

            order = Order.objects.create(customer=customer, total_price=cart.total_price - coupon_discount)
            order.transaction_ref = f"TR-{order.transaction_ref}"

            for item in cart.items.all():
                OrderItem.objects.create(customer=customer, order=order, product=item.product, quantity=item.quantity,
                                         size=item.size, colour=item.colour)
            cart.delete()
        return order

    def to_representation(self, instance: Order):
        items = instance.items.values_list('id', 'product__id', 'product__title', 'quantity')
        return {'id': instance.id, 'customer': instance.customer.full_name,
                'transaction_reference"': instance.transaction_ref, 'total_price': instance.total_price,
                'placed_at': instance.placed_at, 'shipping_status': instance.shipping_status,
                'payment_status': instance.payment_status,
                'items': [{'id': item[0], 'product_id': item[1], 'product__title': item[2], 'quantity': item[3]} for
                          item in items]}

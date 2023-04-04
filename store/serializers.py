import uuid

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from store.models import Cart, CartItem, Colour, Product, ProductReview, Size


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'description', 'style', 'price', 'percentage_off', 'images']

    @staticmethod
    def get_images(obj):
        return [image.image_url() for image in obj.images.all()]


class ProductDetailSerializer(ProductSerializer):
    colours = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    inventory = serializers.IntegerField()
    condition = serializers.CharField()
    location = serializers.CharField()
    discount_price = serializers.DecimalField(max_digits=6, decimal_places=2)
    average_ratings = serializers.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        model = Product
        fields = ProductSerializer.Meta.fields + ['sizes', 'colours', 'inventory', 'condition', 'location',
                                                  'discount_price', 'average_ratings']

    @staticmethod
    def get_colours(obj):
        return obj.colour.values('name', 'hex_code')

    @staticmethod
    def get_sizes(obj):
        return obj.size.values_list('title', flat=True)


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name')

    class Meta:
        model = ProductReview
        fields = ('customer_name', 'ratings', 'description')


class AddProductReviewSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False, max_length=3)

    class Meta:
        model = ProductReview
        fields = ['id', 'ratings', 'description', 'images']

    @staticmethod
    def validate_id(value):
        if not Product.categorized.filter(id=value).exists():
            raise ValidationError("This product does not exist, try again")
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


class AddCartItemSerializer(serializers.Serializer):
    cart_id = serializers.CharField(max_length=60, required=False, default=None)
    product_id = serializers.CharField(max_length=100)
    size = serializers.CharField(required=False)
    colour = serializers.CharField(required=False)
    quantity = serializers.IntegerField()

    def validate(self, attrs):
        product_id = attrs['product_id']
        if not Product.objects.filter(id=product_id).exists():
            raise serializers.ValidationError({"message": "No product with the given ID was found."})

        product = Product.objects.get(id=product_id)
        size = attrs.get('size', '')
        if size and not product.size.filter(title=size).exists():
            raise serializers.ValidationError({"message": "Size not found for the given product.", "status": False})

        colour = attrs.get('colour', '')
        if colour and not product.colour.filter(name=colour).exists():
            raise serializers.ValidationError({"message": "Colour not found for the given product.", "status": False})

        return attrs

    def save(self, **kwargs):
        product = Product.objects.get(id=self.validated_data['product_id'])
        cart_id = self.validated_data.get('cart_id')
        size = self.validated_data.get('size', None)
        colour = self.validated_data.get('colour', None)
        quantity = self.validated_data.get('quantity')

        if cart_id is None:
            cart = Cart.objects.create()
            cart_id = cart.id
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
    pass
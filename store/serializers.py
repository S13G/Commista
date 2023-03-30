from rest_framework import serializers

from store.models import Product, ProductReview


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

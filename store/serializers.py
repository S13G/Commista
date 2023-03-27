from rest_framework import serializers

from store.models import Product


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'category', 'description', 'style', 'price', 'percentage_off', 'size',
                  'colour', 'ratings', 'inventory', 'flash_sale_start_date', 'flash_sale_end_date', 'condition',
                  'location', 'discount_price', 'average_ratings', 'images']

    @staticmethod
    def get_images(obj):
        return [image.image_url() for image in obj.images.all()]

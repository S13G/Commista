from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from store.models import Category, Product


# Create your views here.

class CategoryAndSalesView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.values('id', 'title')
        products_without_flash_sales = Product.categorized.filter(flash_sale_start_date=None, flash_sale_end_date=None)
        flash_sales = Product.categorized.filter(flash_sale_start_date__lte=timezone.now(),
                                                 flash_sale_end_date__gte=timezone.now())
        mega_sales = products_without_flash_sales.filter(percentage_off__gte=24)
        products_without_flash_sales_data = [
            {'title': p.title, 'slug': p.slug, 'images': [image.image_url for image in p.images.all()],
             'price': p.price, 'percentage_off': p.percentage_off, 'ratings': p.average_ratings,
             'discount_price': p.discount_price} for p in products_without_flash_sales]
        flash_sales_data = [
            {'title': fs.title, 'slug': fs.slug, 'images': [image.image_url for image in fs.images.all()],
             'price': fs.price, 'percentage_off': fs.percentage_off, 'ratings': fs.average_ratings,
             'discount_price': fs.discount_price} for fs in flash_sales]
        mega_sales_data = [
            {'title': ms.title, 'slug': ms.slug, 'images': [image.image_url for image in ms.images.all()],
             'price': ms.price, 'percentage_off': ms.percentage_off, 'ratings': ms.average_ratings,
             'discount_price': ms.discount_price} for ms in mega_sales]

        data = {'categories': categories, 'product_without_flash_sales': products_without_flash_sales_data,
                'flash_sales': flash_sales_data, 'mega_sales': mega_sales_data}
        return Response({"message": "Fetched all products", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)

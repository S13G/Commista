from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from store.models import Category, FavoriteProduct, Product
from store.serializers import ProductSerializer


# Create your views here.

class CategoryAndSalesView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get(self, request):
        categories = Category.objects.values('id', 'title')
        products_without_flash_sales = Product.categorized.filter(flash_sale_start_date=None, flash_sale_end_date=None)
        flash_sales = Product.categorized.filter(flash_sale_start_date__lte=timezone.now(),
                                                 flash_sale_end_date__gte=timezone.now())
        serializer = self.serializer_class(many=True)
        mega_sales = products_without_flash_sales.filter(percentage_off__gte=24)
        products_without_flash_sales_data = serializer.to_representation(products_without_flash_sales)
        flash_sales_data = serializer.to_representation(flash_sales)
        mega_sales_data = serializer.to_representation(mega_sales)

        data = {'categories': categories, 'product_without_flash_sales': products_without_flash_sales_data,
                'flash_sales': flash_sales_data, 'mega_sales': mega_sales_data}
        return Response({"message": "Fetched all products", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)


class FavouriteProductsView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user is None:
            return Response({"message": "User does not exist", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        favourite_products = FavoriteProduct.objects.filter(customer=user)

        data = [
            {
                "title": product.title,
                "slug": product.slug,
                "category": product.category.name,
                "description": product.description,
                "style": product.style,
                "price": product.price,
                "percentage_off": product.percentage_off,
                "size": product.size.values_list("name", flat=True),
                "colour": product.colour.values_list("name", flat=True),
                "ratings": product.ratings,
                "inventory": product.inventory,
                "flash_sale_start_date": product.flash_sale_start_date,
                "flash_sale_end_date": product.flash_sale_end_date,
                "condition": product.condition,
                "location": product.location.name,
                "discount_price": product.discount_price,
                "average_ratings": product.average_ratings,
                "images": [image.image_url for image in product.images.all()]
            } for product in favourite_products.all()
        ]
        return Response({"message": "All favourite products fetched", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        product_id = request.data.get("id")
        if product_id is None:
            return Response({"message": "You can't proceed without filling in the field", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        product = Product.objects.filter(id=product_id)
        if not product:
            return Response({"message": "Wrong product id or product does not exist", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        favourite, created = FavoriteProduct.objects.filter(customer=user, product_id=product)
        return Response({"message": "Product added to favourites list", "status": "failed"}, status=status.HTTP_200_OK)

from django.urls import path
from store import views


urlpatterns = [
    path("sales-products-categories/", views.CategoryAndSalesView.as_view(), name="category_product_sales"),
    path("favourite-products/", views.FavouriteProductsView.as_view(), name="favourite_products"),
]
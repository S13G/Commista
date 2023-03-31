from django.urls import path

from store import views

urlpatterns = [
    path("sales-products-categories/", views.CategoryAndSalesView.as_view(), name="category_product_sales"),
    path("favourite-products/", views.FavoriteProductsView.as_view(), name="favourite_products"),
    path("product-detail/<str:product_id>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("add-product-review/", views.AddProductReviewView.as_view(), name="add_product_review"),
]

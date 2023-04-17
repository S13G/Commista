from django.urls import path

from store import views


urlpatterns = [
    path("product-reviews/add/", views.AddProductReviewView.as_view(), name="add_product_review"),
    path("categories/all/", views.CategoryListView.as_view(), name="category_list"),
    path("cart/items/", views.CartItemView.as_view(), name="cart"),
    path("favorites/", views.FavoriteProductsView.as_view(), name="favorite_products"),
    path("notifications/all/", views.NotificationView.as_view(), name="notifications"),
    path("products/<str:product_id>/details/", views.ProductDetailView.as_view(), name="product_detail"),
    path("categories/all-with-sales/", views.CategoryAndSalesView.as_view(), name="category_product_sales"),
    path("products/search-filters/", views.ProductsFilterView.as_view(), name="products_search_and_filters"),
]

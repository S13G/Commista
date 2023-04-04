from django.urls import path

from store import views

urlpatterns = [
    path("add-product-review/", views.AddProductReviewView.as_view(), name="add_product_review"),
    path("category-list/", views.CategoryListView.as_view(), name="category_list"),
    path("cart/items/", views.CartItemView.as_view(), name="cart"),
    path("favourite-products/", views.FavoriteProductsView.as_view(), name="favourite_products"),
    path("notifications/", views.NotificationView.as_view(), name="notifications"),
    path("product-detail/<str:product_id>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("sales-products-categories/", views.CategoryAndSalesView.as_view(), name="category_product_sales"),
    path("search-and-filters/", views.ProductsFilterView.as_view(), name="products_search"),
]

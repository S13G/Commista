from django.urls import path

from store import views

urlpatterns = [
    path('address/', views.ListAndCreateAddressView.as_view(), name='address'),
    path('address/<str:address_id>/details/', views.UpdateAndDeleteAddressView.as_view(), name='address_details'),
    path("cart/items/", views.CartItemView.as_view(), name="cart"),
    path("categories/all/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/all-with-sales/", views.CategoryAndSalesView.as_view(), name="category_product_sales"),
    path("favorites/", views.FavoriteProductsView.as_view(), name="favorite_products"),
    path("countries/", views.CountryView.as_view(), name="countries"),
    path("notifications/all/", views.NotificationView.as_view(), name="notifications"),
    path('orders/', views.CreateOrderView.as_view(), name='create_order'),
    path("product-reviews/add/", views.AddProductReviewView.as_view(), name="add_product_review"),
    path("products/search-filters/", views.ProductsFilterView.as_view(), name="products_search_and_filters"),
    path("products/<str:product_id>/details/", views.ProductDetailView.as_view(), name="product_detail"),
    path("verify-payment/", views.VerifyPaymentView.as_view(), name="verify-payment")
]

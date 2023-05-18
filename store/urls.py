from django.urls import path

from store import views

urlpatterns = [
    path('address/', views.ListCreateAddressView.as_view(), name='address'),
    path('address/<str:address_id>/details/', views.UpdateDeleteAddressView.as_view(), name='address_details'),
    path("cart/items/<str:cart_id>/", views.ListCartItemView.as_view(), name="list_cart_items"),
    path("cart/items/", views.CreateUpdateDeleteCartItemView.as_view(), name="cart_items"),
    path("categories/all/", views.ListCategoryView.as_view(), name="category_list"),
    path("categories/all-with-sales/", views.CategorySalesView.as_view(), name="category_product_sales"),
    path("favorites/", views.FavoriteProductsView.as_view(), name="favorite_products"),
    path("countries/", views.CountryView.as_view(), name="countries"),
    path("notifications/all/", views.ListNotificationView.as_view(), name="notifications"),
    path('orders/', views.ListCreateOrderView.as_view(), name='list_create_order'),
    path('orders/<str:transaction_ref>/delete/', views.DeleteOrderView.as_view(), name='delete_order'),
    path('orders/address/', views.CreateOrderAddress.as_view(), name='order_address'),
    path("product-reviews/add/", views.CreateProductReviewView.as_view(), name="add_product_review"),
    path("products/search-filters/", views.ProductsFilterView.as_view(), name="products_search_and_filters"),
    path("products/<str:product_id>/details/", views.ProductDetailView.as_view(), name="product_detail"),
    path("payments/<str:tx_ref>/verify/", views.VerifyPaymentView.as_view(), name="verify-payment")
]

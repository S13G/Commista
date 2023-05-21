from django.urls import path

from store import views

urlpatterns = [
    path("address/", views.AddressListCreateView.as_view(), name="address"),
    path("address/<str:address_id>/details/", views.AddressUpdateDeleteView.as_view(), name="address_details"),
    path("cart/items/<str:cart_id>/", views.CartItemsListView.as_view(), name="list_cart_items"),
    path("cart/items/", views.CartItemCreateUpdateDeleteView.as_view(), name="cart_items"),
    path("categories/all/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/all-with-sales/", views.CategorySalesView.as_view(), name="category_product_sales"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("checkout/order/address/", views.CheckoutOrderAddressCreateView.as_view(), name="checkout_order_address"),
    path("coupon-codes/", views.CouponCodeView.as_view(), name="coupon_codes"),
    path("favorite-products/", views.FavoriteProductsListView.as_view(), name="favorite_products_list"),
    path("favorite-products/<str:product_id>/", views.FavoriteProductView.as_view(),
         name="favorite_product"),
    path("notifications/all/", views.NotificationListView.as_view(), name="notifications"),
    path("orders/", views.OrderListView.as_view(), name="list_order"),
    path("orders/<str:transaction_ref>/delete/", views.OrderDeleteView.as_view(), name="delete_order"),
    path("product-reviews/add/", views.ProductReviewCreateView.as_view(), name="add_product_review"),
    path("products/search-filters/", views.FilteredProductListView.as_view(), name="products_search_and_filters"),
    path("products/<str:product_id>/details/", views.ProductDetailView.as_view(), name="product_detail"),
    path("payments/<str:tx_ref>/verify/", views.VerifyPaymentView.as_view(), name="verify-payment")
]

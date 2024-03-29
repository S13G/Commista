import requests
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from store.choices import GENDER_FEMALE, GENDER_KIDS, GENDER_MALE, PAYMENT_COMPLETE, PAYMENT_FAILED, \
    SHIPPING_STATUS_PROCESSING
from store.filters import ProductFilter
from store.mixins import GetOrderByTransactionRefMixin
from store.models import Address, Category, ColourInventory, CouponCode, FavoriteProduct, Notification, Order, Product, \
    ProductReview, ProductReviewImage, SizeInventory
from store.serializers import AddCartItemSerializer, AddCheckoutOrderAddressSerializer, AddProductReviewSerializer, \
    AddressSerializer, CartItemSerializer, CheckoutSerializer, CreateAddressSerializer, DeleteCartItemSerializer, \
    FavoriteProductSerializer, OrderListSerializer, OrderSerializer, ProductDetailSerializer, ProductReviewSerializer, \
    ProductSerializer, UpdateCartItemSerializer
from store.throttle import AuthenticatedScopeRateThrottle


# Create your views here.
class AddressListCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateAddressSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Get addresses",
            description=
            """
            Retrieve all addresses or a specific address of the authenticated user.
            """,
            parameters=[
                OpenApiParameter(name="address_id", description="ID of the address (optional)", required=False),
            ],
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Addresses retrieved successfully",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Address not found",
                )
            }
    )
    def get(self, request):
        address_id = self.request.query_params.get('address_id')
        if address_id:
            try:
                address = Address.objects.get(id=address_id, customer=self.request.user)
                serializer = AddressSerializer(address)
                return Response(
                        {"message": "Address retrieved successfully", "data": serializer.data, "status": "success"},
                        status=status.HTTP_200_OK)
            except Address.DoesNotExist:
                return Response({"message": "Address not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        else:
            addresses = Address.objects.filter(customer=self.request.user)
            if not addresses.exists():
                return Response({"message": "Customer has no addresses", "status": "success"},
                                status=status.HTTP_200_OK)
            serializer = AddressSerializer(addresses, many=True)
            return Response(
                    {"message": "All addresses retrieved successfully", "data": serializer.data, "status": "success"},
                    status=status.HTTP_200_OK)

    @extend_schema(
            summary="Add address",
            description=
            """
            Add a new address for the authenticated user.
            """,
            responses={
                status.HTTP_201_CREATED: OpenApiResponse(
                        description="Address added successfully",
                ),
            }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Address added successfully", "data": serializer.data},
                        status=status.HTTP_201_CREATED)


class AddressUpdateDeleteView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateAddressSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Update Address",
            description=
            """
            Update an existing address.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Address updated successfully",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Address not found",
                ),
            }
    )
    def patch(self, request, *args, **kwargs):
        address_id = self.kwargs.get('address_id')
        try:
            address = Address.objects.get(id=address_id, customer=self.request.user)
        except Address.DoesNotExist:
            return Response({"message": "Address not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(address, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Address updated successfully", "data": serializer.data, "status": "success"},
                        status=status.HTTP_200_OK)

    @extend_schema(
            summary="Delete Address",
            description=
            """
            Delete an existing address.
            """,
            responses={
                status.HTTP_204_NO_CONTENT: OpenApiResponse(
                        description="Address deleted successfully",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Address not found",
                ),
            }
    )
    def delete(self, request, *args, **kwargs):
        address_id = self.kwargs.get('address_id')
        try:
            address = Address.objects.get(id=address_id, customer=self.request.user)
        except Address.DoesNotExist:
            return Response({"message": "Address not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response({"message": "Address deleted successfully", "status": "success"},
                        status=status.HTTP_204_NO_CONTENT)


class CartItemCreateUpdateDeleteView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Create Cart Items",
            description=
            """
            Create cart items.
            - To add a new cart item, make a POST request with the required data.
            The request should include the following data:
            - `product_id`: ID of the product to be added.
            - `size`: Size of the product to added, if None, leave blank
            - `colour`: Color of the product to added, if None, leave blank
            - `quantity`: Quantity of the product to be added and you can update item quantity by making
                another post request and only changing the quantity and specify the cart_id too.
        
            If the cart item is added successfully, the response will include the following data:
            - `message`: A success message indicating that the cart item has been added successfully.
            - `data`: The serialized representation of the added cart item.
            - `status`: The status of the request.
            """,
            responses={
                status.HTTP_201_CREATED: OpenApiResponse(
                        description="Cart item added successfully",
                        response=CartItemSerializer,
                ),
            }
    )
    def post(self, request):
        serializer = self.get_serializer(data=self.request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()
        cart_item_data = CartItemSerializer(cart_item, context={'request': request}).data
        return Response(
                {"message": "Cart item added successfully", "data": cart_item_data, "status": "success"},
                status=status.HTTP_201_CREATED
        )

    @extend_schema(
            summary="Update Cart Items",
            description=
            """
            Update cart items.
            - To update an existing cart item, make a PATCH request with the required data.
            The request should include the following data:
            - `cart_id`: ID of the cart containing the item.
            - `product_id`: ID of the product to be updated.
            - `size`: Size of the product to added, if None, leave blank
            - `colour`: Color of the product to added, if None, leave blank
            - `quantity`: Updated quantity of the product.

            If the cart item is added successfully, the response will include the following data:
            - `message`: A success message indicating that the cart item has been added successfully.
            - `data`: The serialized representation of the added cart item.
            - `status`: The status of the request.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Cart item updated successfully",
                        response=CartItemSerializer,
                ),
            }
    )
    def patch(self, request):
        serializer = self.get_serializer(data=self.request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        updated_cart_item = serializer.save()
        updated_cart_item_data = CartItemSerializer(updated_cart_item, context={'request': request}).data
        return Response(
                {"message": "Cart item updated successfully", "data": updated_cart_item_data, "status": "success"},
                status=status.HTTP_200_OK)

    @extend_schema(
            summary="Delete/Remove Cart Items",
            description=
            """
            Delete/Remove cart items.
            - To delete an existing cart item, make a DELETE request with the required data.
            The request should include the following data:
            - `cart_id`: ID of the cart containing the item.
            - `product_id`: ID of the product to be updated.

            If the cart item is deleted successfully, the response will include the following data:
            - `message`: A success message indicating that the cart item has been deleted successfully.
            - `status`: The status of the request.
            """,
            responses={
                status.HTTP_204_NO_CONTENT: OpenApiResponse(
                        description="Cart item deleted successfully",
                ),
            }
    )
    def delete(self, request):
        serializer = self.get_serializer(data=self.request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Item deleted successfully.", "status": "success"},
                        status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        elif self.request.method == "DELETE":
            return DeleteCartItemSerializer
        else:
            return super().get_serializer_class()


class CartItemsListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Retrieve Cart Items",
            description=
            """
            This endpoint allows the authenticated user to retrieve the items in their cart.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Cart items retrieved successfully",
                        response=CartItemSerializer,
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Cart not found",
                )
            }
    )
    def get(self, request, *args, **kwargs):
        customer = self.request.user
        cart_id = self.kwargs.get("cart_id")
        if not cart_id:
            return Response({"message": "Cart ID not provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Order.objects.get(id=cart_id, customer=customer)
        except Order.DoesNotExist:
            return Response({"message": "Cart not found", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = CartItemSerializer(cart.order_items.all(), many=True, context={'request': request})
        return Response({"message": "Cart items retrieved successfully", "cart_total": cart.all_total_price,
                         "data": serializer.data, "status": "success"}, status=status.HTTP_200_OK)


class CategoryListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthenticatedScopeRateThrottle]
    throttle_scope = 'category'

    @extend_schema(
            summary="List Categories",
            description=
            """
            Fetches all categories and categorized by gender.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="All categories fetched",
                ),
            }
    )
    def get(self, request):
        all_categories = Category.objects.values('id', 'title')
        women_categories = Category.objects.filter(gender=GENDER_MALE).values('id', 'title')
        men_categories = Category.objects.filter(gender=GENDER_FEMALE).values('id', 'title')
        kids_categories = Category.objects.filter(gender=GENDER_KIDS).values('id', 'title')
        return Response({"message": "All categories fetched", "all_categories": all_categories,
                         "men_categories": men_categories, "women_categories": women_categories,
                         "kids_categories": kids_categories, "status": "success"}, status=status.HTTP_200_OK)


class CategorySalesView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    throttle_classes = [AuthenticatedScopeRateThrottle]
    throttle_scope = 'category'

    @extend_schema(
            summary="Categories and Products",
            description=
            """
            List all categories and products.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Fetched all products",
                        response=ProductSerializer,
                ),
            }
    )
    def get(self, request):
        categories = Category.objects.values('id', 'title', )
        products_without_flash_sales = Product.objects.filter(flash_sale_start_date=None, flash_sale_end_date=None)
        product_with_flash_sales = Product.objects.filter(flash_sale_start_date__lte=timezone.now(),
                                                          flash_sale_end_date__gte=timezone.now())
        mega_sales = products_without_flash_sales.filter(percentage_off__gte=24)

        serializer = self.serializer_class(many=True)

        products_without_flash_sales_data = serializer.to_representation(products_without_flash_sales)
        products_with_flash_sales_data = serializer.to_representation(product_with_flash_sales)
        mega_sales_data = serializer.to_representation(mega_sales)

        data = {'categories': categories, 'product_without_flash_sales': products_without_flash_sales_data,
                'products_with_flash_sales': products_with_flash_sales_data, 'mega_sales': mega_sales_data}
        return Response({"message": "Fetched all products", "data": data, "status": "success"},
                        status=status.HTTP_200_OK)


class CheckoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Create an order",
            description=
            """
            This endpoint allows the authenticated user to create an order.
            """,
            responses={
                status.HTTP_201_CREATED: OpenApiResponse(
                        description="Order created successfully",
                        response=OrderSerializer,
                ),
            }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response({"message": "Order created successfully", "data": serializer.to_representation(order),
                         "status": "success"}, status=status.HTTP_201_CREATED)


class CheckoutOrderAddressCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddCheckoutOrderAddressSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Add delivery address to an order",
            description=
            """
            This endpoint allows the authenticated user to add a delivery address to an order.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Address added to the order successfully.",
                        response=OrderSerializer,
                ),
            }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
                {"message": "Address added to the order successfully.", "status": "success"},
                status=status.HTTP_200_OK
        )


class FavoriteProductView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Add product to favorites",
            description=
            """
            This endpoint allows an authenticated user to add a product to their favorites list.
            """,
            responses={
                status.HTTP_201_CREATED: OpenApiResponse(
                        description="Product added to favorites.",
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                        description="Invalid or missing product ID.",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Product not found.",
                ),
            }
    )
    def post(self, request, *args, **kwargs):
        customer = self.request.user
        product_id = self.kwargs.get("product_id")
        if not product_id:
            return Response({"message": "Product id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Invalid product id", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)

        favorite, created = FavoriteProduct.objects.get_or_create(customer=customer, product=product)

        if created:
            return Response({"message": "Product added to favorites", "status": "success"},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Product already in favorites", "status": "success"}, status=status.HTTP_200_OK)

    @extend_schema(
            summary="Remove product from favorites",
            description=
            """
            This endpoint allows an authenticated user to remove a product to their favorites list.
            """,
            responses={
                status.HTTP_204_NO_CONTENT: OpenApiResponse(
                        description="Product removed from favorites list.",
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                        description="Invalid or missing product ID.",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Product not found.",
                ),
            }
    )
    def delete(self, request, *args, **kwargs):
        customer = self.request.user
        product_id = self.kwargs.get("product_id")
        if not product_id:
            return Response({"message": "Product id is required", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Invalid product id", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)

        FavoriteProduct.objects.filter(customer=customer, product=product).delete()

        return Response({"message": "Product removed from favorites list", "status": "success"},
                        status=status.HTTP_204_NO_CONTENT)


class CouponCodeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Coupon endpoint",
            description=
            """
            This endpoint gets all available coupons.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="All coupons fetched.",
                ),
            }
    )
    def get(self, request):
        coupon_codes = CouponCode.objects.values('id', 'code', 'price', 'expired', 'expiry_date')
        return Response({"message": "All coupons fetched", "data": coupon_codes, "status": "success"},
                        status=status.HTTP_200_OK)


class FavoriteProductsListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteProductSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Retrieves all favorite products",
            description=
            """
            This endpoint allows an authenticated user to retrieve their favorite products list.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="All favorite products fetched.",
                        response=ProductSerializer(many=True)
                ),
            }
    )
    def get(self, request):
        customer = self.request.user
        if customer is None:
            return Response({"message": "Customer does not exist", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        favorite_products = FavoriteProduct.objects.filter(customer=customer) \
            .select_related('product') \
            .prefetch_related('product__color_inventory__colour',
                              'product__size_inventory__size',
                              'product__images')
        serializer = self.serializer_class(favorite_products, many=True)
        return Response({"message": "All favorite products fetched", "data": serializer.data, "status": "success"},
                        status=status.HTTP_200_OK)


class FilteredProductListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    queryset = Product.objects.all()
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Filtered Product List",
            description=
            """
            This endpoint retrieves a list of filtered products.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Products filtered successfully.",
                        response=ProductSerializer(many=True)
                ),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                        description="Authentication credentials were not provided."
                ),
            },
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True)
        return Response({"message": "Products filtered successfully", "data": serializer.data, "status": "success"},
                        status.HTTP_200_OK)


class NotificationListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Notifications",
            description=
            """
            This endpoint fetches all notifications.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Notifications fetched.",
                ),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                        description="Authentication credentials were not provided."
                ),
            },
    )
    def get(self, request):
        customer = self.request.user
        if customer.is_staff:
            notifications = Notification.objects.all().values('notification_type', 'title', 'description', 'created')
        else:
            notifications = Notification.objects.filter(Q(customers__in=[customer]) | Q(general=True)).values(
                    'notification_type', 'title', 'description', 'created')
        return Response({"message": "Notifications fetched", "data": notifications, "status": "success"},
                        status.HTTP_200_OK)


class OrderListView(GetOrderByTransactionRefMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Get Order List",
            description=
            """
            Retrieve a list of orders for the authenticated customer or a specific order by transaction reference.
            """,
            parameters=[
                OpenApiParameter(name="transaction_ref",
                                 description="Transaction reference of the specific order to retrieve (optional)",
                                 required=False),
            ],
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Order retrieved successfully",
                        response=OrderListSerializer,
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Order not found",
                )
            }
    )
    def get(self, request, *args, **kwargs):
        transaction_reference = self.request.query_params.get('transaction_ref')
        customer = self.request.user
        if transaction_reference:
            order = self._get_order_by_transaction_ref(transaction_reference, request)
            if order is None:
                return Response({"message": "Order not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
            serializer = OrderSerializer(order)
            return Response(
                    {"message": "Order retrieved successfully", "data": serializer.data, "status": "success"},
                    status=status.HTTP_200_OK)

        else:
            all_orders = Order.objects.filter(customer=customer)
            if not all_orders.exists():
                return Response({"message": "Customer has no orders", "status": "success"}, status=status.HTTP_200_OK)
            serializer = OrderListSerializer(all_orders, many=True)
            return Response(
                    {"message": "All orders retrieved successfully", "data": serializer.data, "status": "success"},
                    status=status.HTTP_200_OK)


class OrderDeleteView(GetOrderByTransactionRefMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Delete existing order",
            description=
            """
            Delete an existing order.
            """,
            responses={
                status.HTTP_204_NO_CONTENT: OpenApiResponse(
                        description="Order deleted successfully",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Order not found",
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                        description="Transaction reference is required",
                ),
            }
    )
    def delete(self, request, *args, **kwargs):
        transaction_reference = self.kwargs.get('transaction_ref')
        if not transaction_reference:
            return Response({"message": "Transaction reference is required."}, status=status.HTTP_400_BAD_REQUEST)
        order = self._get_order_by_transaction_ref(transaction_reference, request)
        if order is None:
            return Response({"message": "Order not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        order.delete()
        return Response({"message": "Order deleted successfully.", "status": "success"},
                        status=status.HTTP_204_NO_CONTENT)


class ProductDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Product Detail",
            description=
            """
            Get the details of a specific product, along with related products and reviews.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Product successfully fetched",
                        response=ProductDetailSerializer,
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="This product does not exist, try again",
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                        description="Product ID is required",
                ),
            }
    )
    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get("product_id")
        if product_id is None:
            return Response({"message": "Product ID is required", "status": "success"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"message": "This product does not exist, try again", "status": "failed"},
                            status=status.HTTP_404_NOT_FOUND)
        related_products = product.category.products.exclude(id=product_id)[:10]
        product_serializer = self.get_serializer(product)
        related_products_serializer = ProductSerializer(related_products, many=True)
        product_reviews = product.product_reviews.select_related('customer')
        product_review_serializer = ProductReviewSerializer(product_reviews, many=True)
        return Response({"message": "Product successfully fetched",
                         "data": {
                             "product_details": product_serializer.data,
                             "related_products": related_products_serializer.data,
                             "product_reviews": product_review_serializer.data
                         }, "status": "success"}, status=status.HTTP_200_OK)


class ProductReviewCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddProductReviewSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            summary="Create a product review",
            description=
            """
            This endpoint allows an authenticated user to create a review for a product.
            """,
            responses={
                status.HTTP_201_CREATED: OpenApiResponse(
                        description="Review created successfully",
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                        description="Bad request. Maximum number of allowed images exceeded.",
                ),
            }
    )
    def post(self, request):
        customer = self.request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data.get('product_id')
        product = Product.objects.get(id=product_id)
        images = request.FILES.getlist('images')
        if len(images) > 3:
            return Response({"message": "The maximum number of allowed images is 3", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        product_review = ProductReview.objects.create(customer=customer, product=product, **serializer.validated_data)
        for image in images:
            ProductReviewImage.objects.create(product_review=product_review, _image=image)
        return Response({"message": "Review created successfully", "status": "success"}, status.HTTP_201_CREATED)


class VerifyPaymentView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthenticatedScopeRateThrottle]
    throttle_scope = 'payment'

    @extend_schema(
            summary="Verify Payment",
            description=
            """
            This endpoint allows the authenticated user to verify a payment for an order.
            Retrieves the order based on the provided transaction reference (`tx_ref`) and verifies the payment.
            If the payment is successful, updates the order's payment and shipping status.
    
            - `tx_ref`: The transaction reference of the order.
            """,
            responses={
                status.HTTP_200_OK: OpenApiResponse(
                        description="Product successfully fetched",
                ),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(
                        description="Customer does not have an order with this transaction reference.",
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                        description="This order is missing an address OR "
                                    "Payment verification failed. Please make a payment OR "
                                    "Invalid payment amount",
                ),
                status.HTTP_406_NOT_ACCEPTABLE: OpenApiResponse(
                        description="Invalid payment amount. Please make a payment with the correct amount."
                ),
                status.HTTP_417_EXPECTATION_FAILED: OpenApiResponse(
                        description="Payment failed"
                )
            }
    )
    def get(self, request, *args, **kwargs):
        customer = self.request.user
        tx_ref = self.kwargs.get('tx_ref')

        try:
            order = get_object_or_404(Order, customer=customer, transaction_ref=tx_ref)
        except Http404:
            return Response(
                    {"message": f"Customer does not have an order with this transaction reference {tx_ref}",
                     "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        if order.address is None:
            return Response({"message": "This order is missing an address", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)
        url = f"{settings.FW_VERIFY_LINK}{tx_ref}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {settings.FW_KEY}"
        }
        try:
            response = requests.get(url, headers=headers).json()
            response_data = response.get('data')
            response_status = response_data.get('status')
        except Exception as e:
            return Response(
                    {"message": f"Payment verification failed. Please make a payment. {e}", "status": "failed"},
                    status=status.HTTP_400_BAD_REQUEST)
        if response_status != 'successful':
            order.payment_status = PAYMENT_FAILED
            order.save()
            return Response({"message": "Payment failed", "status": "failed"},
                            status=status.HTTP_417_EXPECTATION_FAILED)
        response_amount = response_data.get('charged_amount')
        if response_amount is None:
            return Response({"message": "Invalid payment amount", "status": "failed"},
                            status=status.HTTP_400_BAD_REQUEST)

        if float(order.all_total_price) > float(response_amount):
            return Response({"message": "Invalid payment amount. Please make a payment with the correct amount.",
                             "status": "failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        order.payment_status = PAYMENT_COMPLETE
        order.shipping_status = SHIPPING_STATUS_PROCESSING
        order.save()
        for item in order.order_items.all():
            item.ordered = True
            item.product.inventory -= item.quantity
            item.product.save()

            if item.size:
                try:
                    item_size_inventory = get_object_or_404(SizeInventory, product=item.product,
                                                            size__title__iexact=item.size)
                except Http404:
                    return Response({"message": "Size not found in size inventory", "status": "failed"},
                                    status=status.HTTP_404_NOT_FOUND)
                item_size_inventory.quantity -= item.quantity
                item_size_inventory.save()

            if item.colour:
                try:
                    item_colour_inventory = get_object_or_404(ColourInventory, product=item.product,
                                                              colour__name__iexact=item.colour)
                except Http404:
                    return Response({"message": "Colour not found in colour inventory", "status": "failed"},
                                    status=status.HTTP_404_NOT_FOUND)
                item_colour_inventory.quantity -= item.quantity
                item_colour_inventory.save()
            item.save()
        return Response({"message": "Payment successful", "status": "success"}, status=status.HTTP_200_OK)

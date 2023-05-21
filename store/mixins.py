from django.http import Http404
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from store.models import Order


class GetOrderByTransactionRefMixin:
    @staticmethod
    def _get_order_by_transaction_ref(transaction_reference, request):
        customer = request.user
        try:
            order = get_object_or_404(Order, customer=customer, transaction_ref=transaction_reference)
        except Http404:
            return Response({"message": "Order not found", "status": "failed"}, status=status.HTTP_404_NOT_FOUND)
        return order

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
            order = Order.objects.get(customer=customer, transaction_ref=transaction_reference)
        except Order.DoesNotExist:
            return None
        return order

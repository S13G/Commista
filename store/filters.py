from django_filters.rest_framework import FilterSet, filters


class ProductFilter(FilterSet):
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    price = filters.NumericRangeFilter(field_name='price', lookup_expr='range')
    condition = filters.ChoiceFilter(field_name='condition', lookup_expr='exact')
    location = filters.CharFilter(field_name='location__location', lookup_expr='icontains')
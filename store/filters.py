from django_filters.rest_framework import FilterSet, filters

from store.choices import CONDITION_CHOICES, GENDER_CHOICES


class ProductFilter(FilterSet):
    gender = filters.ChoiceFilter(field_name='category__gender', lookup_expr='exact', choices=GENDER_CHOICES)
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    price = filters.NumericRangeFilter(field_name='price', lookup_expr='range')
    condition = filters.ChoiceFilter(field_name='condition', lookup_expr='exact', choices=CONDITION_CHOICES)
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')

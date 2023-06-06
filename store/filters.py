from django_filters.rest_framework import FilterSet, filters

from store.choices import CONDITION_CHOICES, GENDER_CHOICES


class ProductFilter(FilterSet):
    gender = filters.ChoiceFilter(field_name='category__gender', lookup_expr='exact', choices=GENDER_CHOICES)
    title = filters.CharFilter(lookup_expr='icontains')
    price = filters.NumericRangeFilter(lookup_expr='range')
    condition = filters.ChoiceFilter(lookup_expr='exact', choices=CONDITION_CHOICES)
    location = filters.CharFilter(lookup_expr='icontains')

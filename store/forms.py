from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import inlineformset_factory
from django.forms.utils import ErrorList

from store.models import ColourInventory, Product, SizeInventory


class ColourInventoryForm(forms.ModelForm):
    class Meta:
        model = ColourInventory
        fields = '__all__'


class SizeInventoryForm(forms.ModelForm):
    class Meta:
        model = SizeInventory
        fields = '__all__'


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    @transaction.atomic
    def check_inventory(self):
        product = self.instance
        if not product:
            if (
                    not ColourInventory.objects.filter(product__title=self.data.get("title")).exists()
                    or SizeInventory.objects.filter(product__title=self.data.get("title")).exists()
            ):
                # Get the inline formset for the ColourInventoryInline
                ColourInventoryFormSet = inlineformset_factory(Product, ColourInventory, form=ColourInventoryForm,
                                                               extra=0)
                color_formset = ColourInventoryFormSet(instance=product, data=self.data)
                color_total_quantity = 0
                for form in color_formset:
                    if form.is_valid():
                        quantity = form.cleaned_data.get('quantity')
                        color_total_quantity += quantity

                SizeInventoryFormSet = inlineformset_factory(Product, SizeInventory, form=SizeInventoryForm, extra=0)
                size_formset = SizeInventoryFormSet(instance=product, data=self.data)
                size_total_quantity = 0
                for form in size_formset:
                    if form.is_valid():
                        quantity = form.cleaned_data.get('quantity')
                        size_total_quantity += quantity

                total_quantity = color_total_quantity + size_total_quantity
                if total_quantity > int(self.data.get("inventory")):
                    raise ValidationError('inventory',
                                   "Total color and size total quantity cannot be greater than total inventory quantity")

                # Return the form instance, either with errors or validated data
                return self
        else:
            # Product already exists, no need to validate inventory
            return self


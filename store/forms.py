from django import forms
from django.db import transaction
from django.forms import inlineformset_factory

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
        if product.DoesNotExist or product is not None:
            if (
                    not ColourInventory.objects.filter(product__title=self.data.get("title")).exists()
                    or SizeInventory.objects.filter(product__title=self.data.get("title")).exists()
            ):
                # Get the inline formset for the ColourInventoryInline
                ColourInventoryFormSet = inlineformset_factory(Product, ColourInventory, form=ColourInventoryForm,
                                                               extra=0)
                color_formset = ColourInventoryFormSet(instance=product, data=self.data)
                color_total_quantity = 0

                # Iterate over the formset to get each form since it's a generator class
                for form in color_formset:
                    if form.is_valid():
                        quantity = form.cleaned_data.get('quantity')
                        color_total_quantity += quantity

                # Get the inline formset for the SizeInventoryInline
                SizeInventoryFormSet = inlineformset_factory(Product, SizeInventory, form=SizeInventoryForm, extra=0)
                size_formset = SizeInventoryFormSet(instance=product, data=self.data)
                size_total_quantity = 0
                for form in size_formset:
                    if form.is_valid():
                        quantity = form.cleaned_data.get('quantity')
                        size_total_quantity += quantity

                total_quantity = color_total_quantity + size_total_quantity
                if total_quantity > int(self.data.get("inventory")):
                    return False
                return True
        else:
            # Product already exists, no need to validate inventory
            return self.data.get('inventory')

    def save(self, commit=True):
        # Call the check_inventory method to validate the form data
        form_valid = self.check_inventory()

        if not form_valid:
            # Add an error to the form instead of raising a ValidationError
            self.add_error(None, "Total color and size total quantity cannot be greater than total inventory quantity")
            return None

        # Call the super().save() method to save the form data to the database
        return super().save(commit=commit)
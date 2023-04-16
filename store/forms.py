from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from store.models import ColourInventory, Product, SizeInventory


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        product = self.instance
        if product.DoesNotExist or product is not None:
            if (
                not ColourInventory.objects.filter(
                    product__title=self.data.get("title")
                ).exists()
                or SizeInventory.objects.filter(
                    product__title=self.data.get("title")
                ).exists()
            ):
                # Get the inline formset for the ColourInventoryInline
                ColourInventoryFormSet = inlineformset_factory(
                    Product, ColourInventory, fields="__all__"
                )
                color_formset = ColourInventoryFormSet(instance=product, data=self.data)
                color_total_quantity = 0

                # Iterate over the formset to get each form since it's a generator class

                # Get the inline formset for the SizeInventoryInline
                SizeInventoryFormSet = inlineformset_factory(
                    Product, SizeInventory, fields="__all__"
                )
                size_formset = SizeInventoryFormSet(instance=product, data=self.data)
                size_total_quantity = 0

                color_total_quantity = self.get_formset_total_quantity(color_formset)
                size_total_quantity = self.get_formset_total_quantity(size_formset)

                total_quantity = color_total_quantity + size_total_quantity
                product_inventory = int(self.data.get("inventory"))

                if total_quantity > product_inventory:
                    self.add_error(
                        None,
                        ValidationError(
                            "Total color and size quantities cannot be greater than product's inventory"
                        ),
                    )

        else:
            return cleaned_data

    def get_formset_total_quantity(formset):
        total_quantity = 0

        for form in formset:
            if form.is_valid():
                quantity = form.cleaned_data.get("quantity", 0)
                total_quantity += quantity
        return total_quantity

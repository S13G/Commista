from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from store.models import ColourInventory, Product, SizeInventory


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    # This validates the product's size and colour total quantity to the product inventory
    def clean(self):
        cleaned_data = super().clean()
        product = self.instance

        if not product:
            return cleaned_data

        color_formset = self.get_inline_formset(ColourInventory, product, self.data)
        size_formset = self.get_inline_formset(SizeInventory, product, self.data)

        color_total_quantity = self.get_formset_total_quantity(color_formset)
        size_total_quantity = self.get_formset_total_quantity(size_formset)

        total_quantity = color_total_quantity + size_total_quantity
        product_inventory = int(self.data.get("inventory", ))

        if total_quantity > product_inventory:
            self.add_error(None, ValidationError(
                    "Total color and size quantities cannot be greater than product's inventory"))

        return cleaned_data

    @staticmethod
    def get_inline_formset(inline_model, instance, data):
        inline_formset_factory = inlineformset_factory(Product, inline_model, fields="__all__")
        return inline_formset_factory(instance=instance, data=data)

    @staticmethod
    def get_formset_total_quantity(formset):
        total_quantity = 0
        for form in formset:
            if form.is_valid():
                quantity = form.cleaned_data.get("quantity")
                if quantity is None:
                    quantity = 0
                total_quantity += quantity
        return total_quantity

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum

from store.models import ColourInventory, Product, SizeInventory


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        super().clean()
        flash_sale_start_date = self.cleaned_data.get("flash_sale_start_date")
        flash_sale_end_date = self.cleaned_data.get("flash_sale_end_date")
        if (
                flash_sale_start_date is not None
                and flash_sale_end_date is not None
                and flash_sale_end_date <= flash_sale_start_date
        ):
            raise ValidationError("End date must greater than start date.")
        elif (
                flash_sale_start_date is not None
                and flash_sale_end_date is not None
                and flash_sale_start_date == flash_sale_end_date
        ):
            raise ValidationError("Start date and end date cannot be equal.")

        if self.instance is None:  # Only run validation on create, not update
            if (
                    ColourInventory.objects.filter(product__id=self.cleaned_data["id"]).exists()
                    or SizeInventory.objects.filter(product_id=self.cleaned_data["id"]).exists()
            ):
                color_quantity = ColourInventory.objects.filter(
                        product_id=self.cleaned_data["id"]
                ).aggregate(Sum("quantity"))["quantity__sum"] or 0
                size_quantity = SizeInventory.objects.filter(
                        product_id=self.cleaned_data["id"]
                ).aggregate(Sum("quantity"))["quantity__sum"] or 0
                if color_quantity + size_quantity > self.cleaned_data["inventory"]:
                    raise ValidationError(
                            "Total color and size total quantity cannot be greater than total inventory quantity"
                    )

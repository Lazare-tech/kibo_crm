from django import forms
from .models import StockMovement, Product

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['quantity', 'movement_type', 'reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Arrivage fournisseur, Perte, Vente...'}),
        }
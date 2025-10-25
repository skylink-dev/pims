from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'description', 'image', 'quantity', 'purchase_price', 'asset_code', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded', 'rows':3}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full'}),
            'quantity': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded'}),
            'asset_code': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded'}),
        }

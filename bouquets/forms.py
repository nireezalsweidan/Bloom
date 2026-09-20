from django import forms
from .models import Bouquet


class OccasionStyleForm(forms.Form):
    occasion = forms.ChoiceField(choices=Bouquet.Occasion.choices)
    style = forms.ChoiceField(choices=Bouquet.Style.choices)
    budget = forms.DecimalField(required=False, min_value=0, decimal_places=2, max_digits=8)
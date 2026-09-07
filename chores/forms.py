from django import forms

from .models import Chore, Roommate


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['title', 'description', 'assigned_to', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = Roommate.objects.all().order_by('name')

    def clean_title(self) -> str:
        title = self.cleaned_data.get('title')
        if title is not None:
            title = title.strip()
        if not title:
            raise forms.ValidationError("Title cannot be empty.")
        return title

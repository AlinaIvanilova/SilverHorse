from django import forms
from django.contrib.auth.models import User
from .models import Message

class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Отримувач",
        empty_label="Оберіть користувача"
    )
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Твоє повідомлення...'
        }),
        label="Повідомлення"
    )

    class Meta:
        model = Message
        fields = ['receiver', 'text']

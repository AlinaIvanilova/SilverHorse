# userspace/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Message, Note, BlockedUser
from .models import EquestrianComplex


class MessageForm(forms.ModelForm):
    receiver_username = forms.CharField(
        label="Отримувач",
        widget=forms.TextInput(attrs={'placeholder': 'Введіть ім’я користувача'})
    )
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Твоє повідомлення...'}),
        label="Повідомлення"
    )

    class Meta:
        model = Message
        fields = ['text']  # поле receiver обробимо вручну

    def clean_receiver_username(self):
        username = self.cleaned_data.get('receiver_username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Користувача з таким іменем не знайдено.")
        return user


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Заголовок (необов’язково)'}),
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Твоя нотатка...'}),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Текст',
        }


class BlockUserForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Ім'я користувача",
        widget=forms.TextInput(attrs={'placeholder': 'Введіть ім’я користувача'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("Користувача з таким іменем не знайдено.")
        return user




class EquestrianComplexForm(forms.ModelForm):
    class Meta:
        model = EquestrianComplex
        fields = ['location', 'prestige']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select'}),
            'prestige': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

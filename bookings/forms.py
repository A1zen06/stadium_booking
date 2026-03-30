from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        label='Email', 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.com'})
    )
    phone = forms.CharField(
        required=False, 
        label='Телефон', 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 999-99-99'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем класс form-co ntrol ко всем полям
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Введите имя пользователя'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Введите пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Повторите пароль'
        })

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']
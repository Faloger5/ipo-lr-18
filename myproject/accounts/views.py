from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django import forms
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Email')
    full_name = forms.CharField(max_length=200, required=False, label='Полное имя')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
        return user


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            if not hasattr(user, 'profile'):
                from shop.models import UserProfile
                UserProfile.objects.create(user=user)
            
            profile = user.profile
            profile.full_name = form.cleaned_data.get('full_name', '')
            profile.phone = form.cleaned_data.get('phone', '')
            profile.save()

            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация прошла успешно.')
            return redirect('catalog')
        else:
            # Выводим все ошибки формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})
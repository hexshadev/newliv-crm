from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CorretorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nome',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu nome'})
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu sobrenome'})
    )
    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Digite seu e-mail'})
    )
    celular = forms.CharField(
        label='Celular',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '(00) 00000-0000'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'celular')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nome de usuário'
        self.fields['username'].widget.attrs.update({'placeholder': 'Digite seu nome de usuário'})
        self.fields['password1'].label = 'Senha'
        self.fields['password1'].widget.attrs.update({'placeholder': 'Digite sua senha'})
        self.fields['password2'].label = 'Confirme a senha'
        self.fields['password2'].widget.attrs.update({'placeholder': 'Digite a senha novamente'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = True
        
        if commit:
            user.save()
            # Cria o perfil do corretor
            from usuarios.models import Perfil
            perfil, created = Perfil.objects.get_or_create(usuario=user)
            perfil.tipo = 'CORRETOR'
            perfil.celular = self.cleaned_data['celular']
            perfil.save()
        
        return user 
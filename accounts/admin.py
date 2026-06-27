from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import User

# Formulário de Edição
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

# Formulário de Criação (Mudamos para ModelForm puro para aceitar o AbstractBaseUser)
class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Força o hash da senha de forma segura no Admin
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm  # Usa o novo formulário de criação limpo

    ordering = ('-created_at',)
    search_fields = ('email',)
    list_display = ('email', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff')
    readonly_fields = ('created_at', 'last_login')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações', {'fields': ('first_name', 'last_name')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Datas Importantes', {'fields': ('last_login', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')
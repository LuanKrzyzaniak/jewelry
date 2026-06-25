from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'perfil', 'is_staff')
    list_filter = UserAdmin.list_filter + ('perfil',)
    fieldsets = UserAdmin.fieldsets + (
        ('Dados da Joalheria', {'fields': ('perfil', 'telefone')}),
    )

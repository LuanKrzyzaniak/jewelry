from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    class Perfil(models.TextChoices):
        GERENTE  = 'GER', 'Gerente'
        VENDEDOR = 'VEN', 'Vendedor'

    perfil    = models.CharField(max_length=3, choices=Perfil.choices, default=Perfil.VENDEDOR)
    telefone  = models.CharField(max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering            = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name()} [{self.get_perfil_display()}]'

    @property
    def is_gerente(self):
        return self.perfil == self.Perfil.GERENTE

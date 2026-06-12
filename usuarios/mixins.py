from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class GerenteRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_gerente:
            messages.error(request, 'Acesso restrito a gerentes.')
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

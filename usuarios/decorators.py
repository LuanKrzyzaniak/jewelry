from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def gerente_required(view_func):
    @wraps(view_func)
    def _checar_gerente(request, *args, **kwargs):
        if not request.user.is_gerente:
            messages.error(request, 'Acesso restrito a gerentes.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)

    return login_required(_checar_gerente)

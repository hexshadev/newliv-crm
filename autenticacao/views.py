from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
import logging

logger = logging.getLogger(__name__)

# Create your views here.

@ensure_csrf_cookie
def login_view(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if not username or not password:
                messages.error(request, 'Por favor, preencha todos os campos.')
                return render(request, 'registration/login.html')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next', '')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
                logger.warning(f'Tentativa de login falhou para usuário: {username}')
        
        return render(request, 'registration/login.html')
    except Exception as e:
        logger.error(f'Erro no login: {str(e)}')
        messages.error(request, 'Ocorreu um erro ao tentar fazer login. Por favor, tente novamente.')
        return render(request, 'registration/login.html')

@login_required
def logout_view(request):
    try:
        logout(request)
        messages.success(request, 'Você foi desconectado com sucesso.')
    except Exception as e:
        logger.error(f'Erro no logout: {str(e)}')
        messages.error(request, 'Ocorreu um erro ao tentar fazer logout.')
    return redirect('login')

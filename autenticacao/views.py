from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
import logging
import traceback

logger = logging.getLogger(__name__)

# Create your views here.

@ensure_csrf_cookie
def login_view(request):
    try:
        logger.info(f"Método da requisição: {request.method}")
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            logger.info(f"Tentativa de login para usuário: {username}")
            
            if not username or not password:
                messages.error(request, 'Por favor, preencha todos os campos.')
                return render(request, 'registration/login.html')
            
            user = authenticate(request, username=username, password=password)
            logger.info(f"Resultado da autenticação: {'Sucesso' if user else 'Falha'}")
            
            if user is not None:
                try:
                    login(request, user)
                    logger.info(f"Login bem-sucedido para usuário: {username}")
                    return redirect('dashboard')
                except Exception as e:
                    logger.error(f"Erro ao fazer login do usuário: {str(e)}")
                    logger.error(traceback.format_exc())
                    messages.error(request, 'Erro ao fazer login. Por favor, tente novamente.')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
                logger.warning(f'Tentativa de login falhou para usuário: {username}')
        
        return render(request, 'registration/login.html')
    except Exception as e:
        logger.error(f"Erro não tratado no login: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'Ocorreu um erro ao tentar fazer login. Por favor, tente novamente.')
        return render(request, 'registration/login.html')

@login_required
def logout_view(request):
    try:
        username = request.user.username
        logout(request)
        logger.info(f"Logout bem-sucedido para usuário: {username}")
        messages.success(request, 'Você foi desconectado com sucesso.')
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, 'Ocorreu um erro ao tentar fazer logout.')
    return redirect('login')

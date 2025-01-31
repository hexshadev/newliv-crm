from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password

# Create your views here.

@login_required
@require_http_methods(['POST'])
def atualizar_perfil(request):
    try:
        user = request.user
        
        # Atualiza dados do usuário
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        
        # Atualiza senha se fornecida
        password = request.POST.get('password')
        if password:
            user.password = make_password(password)
        
        user.save()
        
        # Atualiza dados do perfil
        perfil = user.perfil
        perfil.telefone = request.POST.get('telefone', perfil.telefone)
        perfil.celular = request.POST.get('celular', perfil.celular)
        
        # Atualiza foto se fornecida
        if 'foto' in request.FILES:
            perfil.foto = request.FILES['foto']
        
        perfil.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

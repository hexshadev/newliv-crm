from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Oportunidade

# Create your views here.

class OportunidadeListView(LoginRequiredMixin, ListView):
    model = Oportunidade
    template_name = 'oportunidades/oportunidade_list.html'
    context_object_name = 'oportunidades'
    paginate_by = 10

class OportunidadeDetailView(LoginRequiredMixin, DetailView):
    model = Oportunidade
    template_name = 'oportunidades/oportunidade_detail.html'
    context_object_name = 'oportunidade'

class OportunidadeCreateView(LoginRequiredMixin, CreateView):
    model = Oportunidade
    template_name = 'oportunidades/oportunidade_form.html'
    fields = ['titulo', 'cliente', 'valor', 'status', 'prioridade', 
              'descricao', 'data_previsao_fechamento']
    success_url = reverse_lazy('oportunidade_list')

    def form_valid(self, form):
        form.instance.responsavel = self.request.user
        messages.success(self.request, 'Oportunidade criada com sucesso!')
        return super().form_valid(form)

class OportunidadeUpdateView(LoginRequiredMixin, UpdateView):
    model = Oportunidade
    template_name = 'oportunidades/oportunidade_form.html'
    fields = ['titulo', 'cliente', 'valor', 'status', 'prioridade', 
              'descricao', 'data_previsao_fechamento']
    success_url = reverse_lazy('oportunidade_list')

    def form_valid(self, form):
        messages.success(self.request, 'Oportunidade atualizada com sucesso!')
        return super().form_valid(form)

class OportunidadeDeleteView(LoginRequiredMixin, DeleteView):
    model = Oportunidade
    template_name = 'oportunidades/oportunidade_confirm_delete.html'
    success_url = reverse_lazy('oportunidade_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Oportunidade excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

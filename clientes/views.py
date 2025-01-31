from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Cliente

# Create your views here.

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10

class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    template_name = 'clientes/cliente_form.html'
    fields = ['nome', 'tipo', 'cpf_cnpj', 'email', 'telefone', 'celular', 
              'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 
              'cep', 'status', 'observacoes']
    success_url = reverse_lazy('cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente criado com sucesso!')
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'clientes/cliente_form.html'
    fields = ['nome', 'tipo', 'cpf_cnpj', 'email', 'telefone', 'celular', 
              'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 
              'cep', 'status', 'observacoes']
    success_url = reverse_lazy('cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente atualizado com sucesso!')
        return super().form_valid(form)

class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cliente excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

from django.shortcuts import render
from .models import Product
from django.views.generic import ListView, DetailView
from .models import Product, Color, Size, Brand

def home(request):
    # 1. Busca os produtos de destaque
    produtos_destaque = Product.objects.filter(
        is_featured=True, 
        variants__stock__gt=0
    ).distinct().prefetch_related('images')[:10]

    # Renderiza enviando os três conjuntos de dados
    return render(request, 'index.html', {
        'produtos': produtos_destaque,
    })

class ProductsListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'products.html'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.all().select_related('brand').prefetch_related('images', 'variants__size')
        
        # 2. Filtros de Hierarquia (URL)
        category_slug = self.kwargs.get('category_slug')
        subcategory_slug = self.kwargs.get('subcategory_slug')
        
        if subcategory_slug:
            queryset = queryset.filter(subcategory__slug=subcategory_slug)
        elif category_slug:
            queryset = queryset.filter(subcategory__category__slug__iexact=category_slug)
        
        # 3. BUSCA
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        # 4. Filtros de QueryString
        brand_slug = self.request.GET.get('marca')
        cor_slug = self.request.GET.get('cor')
        tamanho_slug = self.request.GET.get('tamanho')
        
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)
        if cor_slug:
            queryset = queryset.filter(color__slug=cor_slug)
        if tamanho_slug:
            queryset = queryset.filter(variants__size__slug=tamanho_slug)

        # 5. Ordenação
        ordenacao = self.request.GET.get('preco')
        if ordenacao == 'asc':
            queryset = queryset.order_by('price')
        elif ordenacao == 'desc':
            queryset = queryset.order_by('-price')
        else:
            queryset = queryset.order_by('-created_at')
            
        # .distinct() é importante se você tiver filtros com JOINs complexos
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contexto base
        context['marcas'] = Brand.objects.all().order_by('name')
        context['cores'] = Color.objects.all()
        
        # Slugs para o template
        sub_slug = self.kwargs.get('subcategory_slug')
        context['category_slug'] = self.kwargs.get('category_slug')
        context['subcategory_slug'] = sub_slug
        
        # Lógica inteligente de filtro de tamanhos
        todos_tamanhos = Size.objects.all().order_by('order')
        
        tamanhos_letras = ['camisetas', 'blusas'] 
        tamanhos_numeros = ['footwears', 'calcas']

        if sub_slug in tamanhos_letras:
            # Filtra apenas letras (P, M, G...)
            context['tamanhos'] = [s for s in todos_tamanhos if not s.name.isdigit()]
        elif sub_slug in tamanhos_numeros:
            # Filtra apenas números (38, 40, 42...)
            context['tamanhos'] = [s for s in todos_tamanhos if s.name.isdigit()]
        else:
            # Se não estiver em nenhuma, mostra todos (ou o que fizer sentido para você)
            context['tamanhos'] = todos_tamanhos
        
        return context
    
def QuemSomosView(request):
    return render(request, 'quem_somos.html')

def politica_privacidade(request):
    return render(request, 'politica-de-privacidade.html')

class ProductDetailView(DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'
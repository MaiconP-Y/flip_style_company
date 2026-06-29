from django.shortcuts import render
from .models import Product
from django.views.generic import ListView, DetailView
from .models import Product, Color, Size, Brand, SizeGuide

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
        
        # 1. Captura as variáveis da URL e da QueryString (?marca=...)
        category_slug = self.kwargs.get('category_slug')
        sub_slug = self.kwargs.get('subcategory_slug')
        brand_slug = self.request.GET.get('marca')  # Captura o ?marca= da URL
        
        context['category_slug'] = category_slug
        context['subcategory_slug'] = sub_slug
        
        # 2. Criamos as consultas base para Tamanhos e Cores
        tamanhos_qs = Size.objects.all()
        cores_qs = Color.objects.all()
        
        # 3. Aplicamos o funil de Categorias/Subcategorias se existirem
        if sub_slug:
            tamanhos_qs = tamanhos_qs.filter(variants__product__subcategory__slug=sub_slug)
            cores_qs = cores_qs.filter(products__subcategory__slug=sub_slug)
            
        elif category_slug:
            tamanhos_qs = tamanhos_qs.filter(variants__product__subcategory__category__slug__iexact=category_slug)
            cores_qs = cores_qs.filter(products__subcategory__category__slug__iexact=category_slug)
            
        # 4. AQUI ESTÁ O QUE VOCÊ QUERIA: Se o usuário filtrou por marca, restringe ainda mais!
        if brand_slug:
            tamanhos_qs = tamanhos_qs.filter(variants__product__brand__slug=brand_slug)
            cores_qs = cores_qs.filter(products__brand__slug=brand_slug)
            
        # 5. Entrega os contextos limpos, ordenados e sem duplicadas pro HTML
        context['tamanhos'] = tamanhos_qs.distinct().order_by('order')
        context['cores'] = cores_qs.distinct()
        
        # Mantém suas marcas estáticas livres (ou traz todas do banco)
        context['marcas'] = Brand.objects.all().order_by('name')
        
        return context
    
def QuemSomosView(request):
    return render(request, 'quem_somos.html')

def politica_privacidade(request):
    return render(request, 'politica-de-privacidade.html')

class ProductDetailView(DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'

    def get_queryset(self):
        return Product.objects.all().select_related('brand').prefetch_related('images', 'variants__size')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produto_atual = self.object

        # Busca os 5 últimos produtos da mesma subcategoria, excluindo o produto atual
        context['produtos_recomendados'] = Product.objects.filter(
            subcategory=produto_atual.subcategory
        ).exclude(
            id=produto_atual.id
        ).prefetch_related('images').order_by('-id')[:4]

        return context
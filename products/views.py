from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Product, Color, Size, Brand, SizeGuide, Subcategory, Category, ProductModel
from django.db.models import Q

def home(request):
    # 1. Busca os produtos de destaque (Otimizado com select_related para a nova estrutura)
    produtos_destaque = Product.objects.filter(
        is_featured=True, 
        variants__stock__gt=0
    ).distinct().select_related('product_model__brand').prefetch_related('images')[:10]

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
        # 1. select_related alterado para buscar a marca pelo product_model
        queryset = Product.objects.all().select_related('product_model__brand').prefetch_related('images')
        
        # Filtros de Hierarquia (URL)
        category_slug = self.kwargs.get('category_slug')
        subcategory_slug = self.kwargs.get('subcategory_slug')
        modelo_slug = self.request.GET.get('modelo')
        
        # AJUSTADO: Se vier o modelo, aplica ele. Os outros rodam em paralelo ou na cadeia.
        if modelo_slug:
            queryset = queryset.filter(product_model__slug=modelo_slug)
        
        if subcategory_slug:
            queryset = queryset.filter(product_model__subcategory__slug=subcategory_slug)
        elif category_slug:
            queryset = queryset.filter(product_model__subcategory__category__slug__iexact=category_slug)
        
        # Busca
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        # Filtros Laterais (Query Params)
        brand_slug = self.request.GET.get('marca')
        cor_slug = self.request.GET.get('cor')
        tamanho_slug = self.request.GET.get('tamanho')
        
        if brand_slug:
            queryset = queryset.filter(product_model__brand__slug=brand_slug)
            
        if cor_slug:
            queryset = queryset.filter(color__slug=cor_slug)
            
        if tamanho_slug:
            queryset = queryset.filter(variants__size__slug=tamanho_slug, variants__stock__gt=0)
        else:
            queryset = queryset.filter(variants__stock__gt=0)

        # Ordenação
        ordenacao = self.request.GET.get('preco')
        if ordenacao == 'asc':
            queryset = queryset.order_by('price')
        elif ordenacao == 'desc':
            queryset = queryset.order_by('-price')
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category_slug = self.kwargs.get('category_slug')
        sub_slug = self.kwargs.get('subcategory_slug')
        brand_slug = self.request.GET.get('marca')
        modelo_slug = self.request.GET.get('modelo')

        # CORREÇÃO CRUCIAL: Inicializando brand_name para evitar erro no template
        context['brand_name'] = None
        context['category_name'] = None
        context['subcategory_name'] = None
        context['modelo_name'] = None

        # Criar um filtro base para o estoque das variantes
        product_filter = Q(variants__stock__gt=0)

        # Buscar nome da Marca se o filtro estiver ativo
        if brand_slug:
            brand = Brand.objects.filter(slug=brand_slug).first()
            if brand:
                context['brand_name'] = brand.name
                product_filter &= Q(product_model__brand_id=brand.id)

        # Buscar nome do Modelo se o filtro estiver ativo
        if modelo_slug:
            mod = ProductModel.objects.filter(slug=modelo_slug).first()
            if mod:
                context['modelo_name'] = mod.name
                product_filter &= Q(product_model_id=mod.id)

        # Ajustar os filtros dinâmicos com base na nova tabela
        if sub_slug:
            sub = Subcategory.objects.filter(slug=sub_slug).first()
            if sub:
                context['subcategory_name'] = sub.name
                product_filter &= Q(product_model__subcategory_id=sub.id)
        elif category_slug:
            cat = Category.objects.filter(slug__iexact=category_slug).first()
            if cat:
                context['category_name'] = cat.name
                product_filter &= Q(product_model__subcategory__category_id=cat.id)

        # Buscar os IDs dos produtos filtrados para restringir atributos laterais
        product_ids = Product.objects.filter(product_filter).values_list('id', flat=True).distinct()

        # Injetar os dados para renderizar os filtros laterais dinâmicos
        context['tamanhos'] = Size.objects.filter(
            variants__product_id__in=product_ids,
            variants__stock__gt=0
        ).distinct().order_by('order')
        
        context['cores'] = Color.objects.filter(
            products__id__in=product_ids
        ).distinct()
        
        context['category_slug'] = category_slug
        context['subcategory_slug'] = sub_slug
        context['marcas'] = Brand.objects.all().order_by('name')
        
        return context

class ProductDetailView(DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'

    def get_queryset(self):
        # Ajustado para trazer a marca através do product_model pré-carregado
        return Product.objects.all().select_related('product_model__brand').prefetch_related('images', 'variants__size')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produto_atual = self.object
        
        # 1. Tabela de medidas baseada na marca e subcategoria do product_model
        try:
            context['tabela_medidas'] = SizeGuide.objects.get(
                brand=produto_atual.product_model.brand,
                subcategory=produto_atual.product_model.subcategory
            )
        except SizeGuide.DoesNotExist:
            context['tabela_medidas'] = None
            
        # 2. Busca os produtos recomendados filtrando pelo product_model__subcategory
        recomendados = list(Product.objects.filter(
            product_model__subcategory=produto_atual.product_model.subcategory,
            variants__stock__gt=0
        ).exclude(
            id=produto_atual.id
        ).distinct().select_related('product_model__brand').prefetch_related('images').order_by('-id')[:4])
        
        # 3. Se não alcançou os 4 produtos, preenche o restante com produtos de destaque
        total_desejado = 4
        if len(recomendados) < total_desejado:
            vagas_restantes = total_desejado - len(recomendados)
            
            ids_excluidos = [p.id for p in recomendados] + [produto_atual.id]
            
            destaques_completarem = Product.objects.filter(
                is_featured=True,
                variants__stock__gt=0
            ).exclude(
                id__in=ids_excluidos
            ).distinct().select_related('product_model__brand').prefetch_related('images')[:vagas_restantes]
            
            recomendados.extend(list(destaques_completarem))
            
        context['produtos_recomendados'] = recomendados

        return context

def QuemSomosView(request):
    return render(request, 'quem_somos.html')

def politica_privacidade(request):
    return render(request, 'politica_privacidade.html')
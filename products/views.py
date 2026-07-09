from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from .models import Product, Color, Size, Brand, SizeGuide, Subcategory, Category, ProductModel
from django.db.models import Q
from django.http import Http404

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
        queryset = Product.objects.all().select_related('product_model__brand').prefetch_related('images')
        
        category_slug = self.kwargs.get('category_slug')
        subcategory_slug = self.kwargs.get('subcategory_slug')
        modelo_slug = self.request.GET.get('modelo')
        
        if modelo_slug:
            queryset = queryset.filter(product_model__slug=modelo_slug)
        
        if subcategory_slug:
            queryset = queryset.filter(product_model__subcategory__slug=subcategory_slug)
        elif category_slug:
            queryset = queryset.filter(product_model__subcategory__category__slug__iexact=category_slug)
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

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

        # Ordenação Otimizada
        ordenacao_param = self.request.GET.get('ordenar')
        sort_map = {
            'preco_asc': 'price',
            'preco_desc': '-price',
            'marca_asc': 'product_model__brand__name',
            'marca_desc': '-product_model__brand__name',
        }
        order_by_field = sort_map.get(ordenacao_param, '-created_at')
        return queryset.order_by(order_by_field).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Variáveis base
        category_slug = self.kwargs.get('category_slug')
        sub_slug = self.kwargs.get('subcategory_slug')
        brand_slug = self.request.GET.get('marca')
        modelo_slug = self.request.GET.get('modelo')
        ordenacao_param = self.request.GET.get('ordenar')

        context.update({
            'brand_name': None, 'category_name': None, 
            'subcategory_name': None, 'modelo_name': None,
            'ordenacao_label': None
        })

        if ordenacao_param:
            labels = {
                'preco_asc': 'Menor Preço', 'preco_desc': 'Maior Preço',
                'marca_asc': 'Marca: A - Z', 'marca_desc': 'Marca: Z - A',
            }
            context['ordenacao_label'] = labels.get(ordenacao_param)

        product_filter = Q(variants__stock__gt=0)

        if brand_slug:
            brand = Brand.objects.filter(slug=brand_slug).only('name', 'id').first()
            if brand:
                context['brand_name'] = brand.name
                product_filter &= Q(product_model__brand_id=brand.id)

        if modelo_slug:
            mod = ProductModel.objects.filter(slug=modelo_slug).only('name', 'id').first()
            if mod:
                context['modelo_name'] = mod.name
                product_filter &= Q(product_model_id=mod.id)

        if sub_slug:
            sub = Subcategory.objects.filter(slug=sub_slug).only('name', 'id').first()
            if sub:
                context['subcategory_name'] = sub.name
                product_filter &= Q(product_model__subcategory_id=sub.id)
        elif category_slug:
            cat = Category.objects.filter(slug__iexact=category_slug).only('name', 'id').first()
            if cat:
                context['category_name'] = cat.name
                product_filter &= Q(product_model__subcategory__category_id=cat.id)

        product_ids = Product.objects.filter(product_filter).values_list('id', flat=True).distinct()

        context['tamanhos'] = Size.objects.filter(variants__product_id__in=product_ids, variants__stock__gt=0).distinct().order_by('order')
        context['cores'] = Color.objects.filter(products__id__in=product_ids).distinct()
        context['marcas'] = Brand.objects.all().order_by('name')
        
        return context
    
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # Captura o 404 gerado quando os filtros reduzem o número de páginas
            params = request.GET.copy()
            
            if 'page' in params:
                params.pop('page')  # Remove a página inválida para resetar para a página 1
            
            # Reconstrói a URL preservando os filtros aplicados pelo usuário
            redirect_url = request.path
            if params:
                redirect_url += f"?{params.urlencode()}"
            
            return redirect(redirect_url)

class ProductDetailView(DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'

    def get_queryset(self):
        return Product.objects.all().select_related('product_model__brand').prefetch_related('images', 'variants__size')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produto_atual = self.object
        
        try:
            context['tabela_medidas'] = SizeGuide.objects.get(
                brand=produto_atual.product_model.brand,
                subcategory=produto_atual.product_model.subcategory
            )
        except SizeGuide.DoesNotExist:
            context['tabela_medidas'] = None
            
        # 1. Busca as outras cores do mesmo modelo para as miniaturas (LIMIT 6)
        cores_do_modelo = list(Product.objects.filter(
            product_model=produto_atual.product_model,
            variants__stock__gt=0
        ).exclude(
            id=produto_atual.id
        ).distinct().prefetch_related('images')[:6])
        
        context['cores_do_modelo'] = cores_do_modelo
        
        # 2. MÁGICA "ANTI-REPETIÇÃO": Junta o ID do produto atual com os IDs das miniaturas de cores
        ids_para_excluir = [produto_atual.id] + [p.id for p in cores_do_modelo]
        
        # 3. Busca os destaques garantindo que NADA que já apareceu acima se repita aqui (LIMIT 4)
        context['produtos_recomendados'] = Product.objects.filter(
            is_featured=True,
            variants__stock__gt=0
        ).exclude(
            id__in=ids_para_excluir  # Exclui o atual E as outras cores
        ).distinct().select_related('product_model__brand').prefetch_related('images')[:4]

        return context

def QuemSomosView(request):
    return render(request, 'quem_somos.html')

def PrivacidadeView(request):
    return render(request, 'politica_privacidade.html')
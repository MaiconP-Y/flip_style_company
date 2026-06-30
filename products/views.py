from django.shortcuts import render
from .models import Product
from django.views.generic import ListView, DetailView
from .models import Product, Color, Size, Brand, SizeGuide, Subcategory, Category
from django.db.models import Q

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
        # 1. select_related e prefetch_related cirúrgicos
        queryset = Product.objects.all().select_related('brand').prefetch_related('images')
        
        # Filtros de Hierarquia (URL)
        category_slug = self.kwargs.get('category_slug')
        subcategory_slug = self.kwargs.get('subcategory_slug')
        
        if subcategory_slug:
            queryset = queryset.filter(subcategory__slug=subcategory_slug)
        elif category_slug:
            queryset = queryset.filter(subcategory__category__slug__iexact=category_slug)
        
        # Busca
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        # Filtros de QueryString
        brand_slug = self.request.GET.get('marca')
        cor_slug = self.request.GET.get('cor')
        tamanho_slug = self.request.GET.get('tamanho')
        
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)
        if cor_slug:
            queryset = queryset.filter(color__slug=cor_slug)
            
        # Garante consistência: Se buscou tamanho, valida na mesma variante. 
        # Se não, valida se há qualquer variante com estoque.
        if tamanho_slug:
            queryset = queryset.filter(variants__size__slug=tamanho_slug, variants__stock__gt=0)
        else:
            queryset = queryset.filter(variants__stock__gt=0)

        # Ordenação por índices/campos diretos
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
        
        context['category_name'] = None
        context['subcategory_name'] = None

        # CORREÇÃO 1: O escopo base dos filtros deve OBRIGATORIAMENTE considerar apenas produtos com estoque ativo,
        # igualzinho ao que foi feito no get_queryset. Isso limpa o filtro de cores de produtos esgotados.
        product_filter = Q(variants__stock__gt=0)
        
        if sub_slug:
            sub = Subcategory.objects.filter(slug=sub_slug).first()
            if sub:
                context['subcategory_name'] = sub.name
                product_filter &= Q(subcategory_id=sub.id)
        elif category_slug:
            cat = Category.objects.filter(slug__iexact=category_slug).first()
            if cat:
                context['category_name'] = cat.name
                product_filter &= Q(subcategory__category_id=cat.id)
                
        if brand_slug:
            product_filter &= Q(brand__slug=brand_slug)

        # CORREÇÃO 2: Adicionado .distinct() para o banco gerar uma lista limpa de IDs de produtos,
        # tornando as subqueries subsequentes extremamente rápidas através do índice da PK.
        product_ids = Product.objects.filter(product_filter).values_list('id', flat=True).distinct()

        # Filtros laterais indexados e leves
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
        
        # 1. Busca a tabela vinculada exatamente à MARCA E à SUBCATEGORIA do produto
        try:
            context['tabela_medidas'] = SizeGuide.objects.get(
                brand=produto_atual.brand,
                subcategory=produto_atual.subcategory
            )
        except SizeGuide.DoesNotExist:
            context['tabela_medidas'] = None
            
        # 2. Busca os produtos recomendados da mesma subcategoria que POSSUEM estoque disponível
        # .distinct() inserido antes do slice para evitar problemas de contagem com os JOINs de variantes
        recomendados = list(Product.objects.filter(
            subcategory=produto_atual.subcategory,
            variants__stock__gt=0
        ).exclude(
            id=produto_atual.id
        ).distinct().prefetch_related('images').order_by('-id')[:4])
        
        # 3. Se não alcançou os 4 produtos, preenche o restante com produtos de destaque também em estoque
        total_desejado = 4
        if len(recomendados) < total_desejado:
            vagas_restantes = total_desejado - len(recomendados)
            
            # Coleta os IDs de produtos que JÁ estão nos recomendados + o ID do produto atual
            ids_excluidos = [p.id for p in recomendados] + [produto_atual.id]
            
            destaques_completarem = Product.objects.filter(
                is_featured=True,
                variants__stock__gt=0
            ).exclude(
                id__in=ids_excluidos
            ).distinct().prefetch_related('images')[:vagas_restantes]
            
            # Une as duas listas
            recomendados.extend(list(destaques_completarem))
            
        context['produtos_recomendados'] = recomendados

        return context
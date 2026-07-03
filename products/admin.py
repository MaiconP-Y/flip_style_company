from django import forms  # Certifique-se de importar o forms do Django
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    Category, SizeGuide, Subcategory, Brand, Color, Size, 
    Product, ProductVariant, ProductImage, ProductModel
)

# Configurações globais do painel
admin.site.site_title = "FlipStyle Admin"
admin.site.site_header = "FlipStyle"
admin.site.index_title = "Painel FlipStyle"

# Mapeamento com nomes em String (Boa prática de arquitetura e legível)
MOLDES_TAMANHO = {
    'CAMISETAS_PP_ao_XGG': ['PP', 'P', 'M', 'G', 'GG', 'XGG'],
    'TENIS_34_ao_44': [str(i) for i in range(34, 45)],
    'CALÇAS_BERMUDAS_38_ao_58': [str(i) for i in range(38, 59, 2)],
}


# --- Formulário Customizado (Força o Django a não ignorar estoque 0) ---
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = '__all__'

    def has_changed(self):
        # Se o formulário recebeu dados pelo 'initial' (a nossa grade),
        # nós dizemos ao Django que ele mudou para forçar o INSERT no banco.
        has_changed = super().has_changed()
        return bool(self.initial or has_changed)


# --- Inlines ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 3


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    form = ProductVariantForm  # Acopla a regra de salvamento forçado
    fields = ('size', 'stock', 'order')

    # 1. Define a quantidade exata de linhas a serem abertas na tela
    def get_extra(self, request, obj=None, **kwargs):
        if obj is None and 'grade' in request.GET:
            grade_escolhida = request.GET.get('grade')
            if grade_escolhida in MOLDES_TAMANHO:
                return len(MOLDES_TAMANHO[grade_escolhida])
        return 1  # Padrão do Django se não houver grade na URL

    # 2. Injeta os dados iniciais traduzindo String para o ID numérico do banco
    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)
        
        # A trava 'obj is None' garante que isso SÓ rode ao CRIAR um produto novo
        if obj is None and 'grade' in request.GET:
            grade_escolhida = request.GET.get('grade')
            
            if grade_escolhida in MOLDES_TAMANHO:
                nomes_tamanhos = MOLDES_TAMANHO[grade_escolhida]
                
                # ALTA PERFORMANCE: Faz apenas 1 query SQL trazendo em memória um dicionário {'M': 2, 'G': 3}
                # Evita instanciar objetos complexos e roda em frações de milissegundo.
                tamanhos_db = dict(
                    Size.objects.filter(name__in=nomes_tamanhos).values_list('name', 'id')
                )
                
                class InitialDataFormSet(FormSet):
                    def __init__(self, *args, **kwargs):
                        # Só injeta se for o carregamento inicial da página (GET), não sobrescreve o POST
                        if not args and 'data' not in kwargs:
                            kwargs['initial'] = [
                                {
                                    'size': tamanhos_db.get(nome), 
                                    'stock': 0, 
                                    'order': index + 1
                                }
                                for index, nome in enumerate(nomes_tamanhos)
                                if nome in tamanhos_db
                            ]
                        super().__init__(*args, **kwargs)
                        
                return InitialDataFormSet
                
        return FormSet

# --- Admin Classes ---

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'subcategory')
    list_filter = ('brand', 'subcategory')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductVariantInline]
    list_display = ('name', 'product_model', 'color', 'price', 'is_featured')
    list_editable = ('is_featured', 'product_model')
    list_filter = ('product_model__brand', 'product_model__subcategory', 'color')
    search_fields = ('name', 'product_model__name')
    prepopulated_fields = {'slug': ('name',)}
    
    fields = ('carregar_grade_rapida', 'product_model', 'color', 'name', 'slug', 'price', 'is_featured')
    readonly_fields = ('carregar_grade_rapida',)

    # Mantido exatamente sua lógica original de botões funcionais
    def carregar_grade_rapida(self, obj):
        if obj.pk:  
            return ""
        
        botoes = []
        for nome_grade in MOLDES_TAMANHO.keys():
            url = f"?grade={nome_grade}"
            botoes.append(
                f'<a class="button" style="margin-right: 10px; background: #264b5d; color: #fff; font-weight: bold; padding: 6px 12px; border-radius: 4px;" href="{url}">{nome_grade.upper()}</a>'
            )
        return mark_safe(" ".join(botoes))
    
    carregar_grade_rapida.short_description = "Moldes Rápidos PARA PRIMEIRO CADASTRO"

@admin.register(SizeGuide)
class SizeGuideAdmin(admin.ModelAdmin):
    list_display = ('brand', 'subcategory', 'has_image')
    list_filter = ('brand', 'subcategory')

    def has_image(self, obj):
        return bool(obj.guide_image)
    has_image.boolean = True
    has_image.short_description = "Tem Imagem?"

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)

@admin.register(Category, Brand, Size)
class SimpleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
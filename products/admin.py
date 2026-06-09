from django.contrib import admin
from .models import Category, Subcategory, Brand, Color, Size, Product, ProductVariant, ProductImage

# Mude o título da aba do navegador
admin.site.site_title = "FlipStyle Admin"

# Mude o título principal na página (o que você mostrou na imagem)
admin.site.site_header = "FlipStyle"

# Mude o título da página de índice do admin
admin.site.index_title = "Bem-vindo ao Painel da FlipStyle"

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    max_num = 3

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    

# 2. Único registro para o modelo Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Combinamos todos os atributos aqui:
    inlines = [ProductImageInline, ProductVariantInline]
    list_display = ('name', 'brand', 'price', 'is_featured', 'created_at')
    list_editable = ('is_featured',) # Permite editar direto na lista
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

# 3. Outros registros
@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

# Registros simples
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Color)
admin.site.register(Size)
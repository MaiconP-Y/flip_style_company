from django.contrib import admin
from .models import Category, SizeGuide, Subcategory, Brand, Color, Size, Product, ProductVariant, ProductImage

admin.site.site_title = "FlipStyle Admin"
admin.site.site_header = "FlipStyle"
admin.site.index_title = "Bem-vindo ao Painel da FlipStyle"

@admin.register(SizeGuide)
class SizeGuideAdmin(admin.ModelAdmin):
    list_display = ('brand', 'subcategory', 'has_image') # 'has_image' é um atalho visual
    list_filter = ('brand', 'subcategory')

    def has_image(self, obj):
        return bool(obj.guide_image)
    has_image.boolean = True
    has_image.short_description = "Tem Imagem?"

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    max_num = 3

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'stock', 'order')
    

# 2. Único registro para o modelo Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Combinamos todos os atributos aqui:
    inlines = [ProductImageInline, ProductVariantInline]
    list_display = ('name', 'brand', 'color', 'price', 'is_featured', 'created_at')
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
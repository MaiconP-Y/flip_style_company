from django.contrib import admin
from .models import (
    Category, SizeGuide, Subcategory, Brand, Color, Size, 
    Product, ProductVariant, ProductImage, ProductModel
)

# Configurações globais
admin.site.site_title = "FlipStyle Admin"
admin.site.site_header = "FlipStyle"
admin.site.index_title = "Painel FlipStyle"

# --- Inlines Reutilizáveis ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 3

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'stock', 'order')

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
    # 'brand' e 'subcategory' removidos daqui (pois agora residem em ProductModel)
    list_display = ('name', 'product_model', 'color', 'price', 'is_featured')
    list_editable = ('is_featured', 'product_model')
    list_filter = ('product_model__brand', 'product_model__subcategory', 'color')
    search_fields = ('name', 'product_model__name')
    prepopulated_fields = {'slug': ('name',)}

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

# Registros simples que não precisam de customização complexa
@admin.register(Category, Brand, Size)
class SimpleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',) # Isso é obrigatório para o autocomplete funcionar
    prepopulated_fields = {'slug': ('name',)}
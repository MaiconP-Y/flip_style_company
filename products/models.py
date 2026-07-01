from django.db import models

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from decimal import Decimal

from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Subcategoria"
        verbose_name_plural = "Subcategorias"

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class Brand(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Cor"
        verbose_name_plural = "Cores"

    def __str__(self):
        return self.name


class Product(models.Model):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, related_name='products')
    color = models.ForeignKey(Color, on_delete=models.PROTECT, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_featured = models.BooleanField(default=False, verbose_name="É destaque?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        # O Django trata o __str__ como uma representação de debug.
        # Prefira exibir apenas o que existe.
        parts = [self.name]
        if self.brand:
            parts.insert(0, f"[{self.brand.name}]")
        if self.color:
            parts.append(f" - {self.color.name}")
        return " ".join(parts)

    @property
    def available_sizes(self):
        return list(
            self.variants.filter(stock__gt=0)
            .values_list('size__name', flat=True)
        )
    
    @property
    def preco_parcelado(self):
        return self.price / 12

    @property
    def get_pix_price(self):
        if self.price:
            return (self.price * Decimal('0.95')).quantize(Decimal('0.01'))
        return Decimal('0.00')


class Size(models.Model):
    # O 'name' é o que o cliente vê (P, M, G, 38, 40...)
    name = models.CharField(max_length=20, unique=True)
    # O 'slug' é para a URL (p, m, g, 38, 40...)
    slug = models.SlugField(unique=True)
    
    # Opcional: Um campo para ajudar a ordenar no front-end
    # Isso evita que o front-end mostre "G, P, GG, M" fora de ordem
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")

    class Meta:
        verbose_name = "Tamanho"
        verbose_name_plural = "Tamanhos"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.PROTECT, related_name='variants')
    stock = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="SKU")
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Código de Barras")

    class Meta:
        verbose_name = "Variante de Produto"
        verbose_name_plural = "Variantes de Produtos"
        unique_together = ('product', 'size')
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Tam: {self.size.name} (Estoque: {self.stock})"
    
    def save(self, *args, **kwargs):
        # Se a variante for nova e o campo order não foi preenchido manualmente (continuar 0)
        if not self.id and self.order == 0:
            # Conta quantas variantes esse produto específico já tem e define a sequência
            subsequente = ProductVariant.objects.filter(product=self.product).count() + 1
            self.order = subsequente
        
        super().save(*args, **kwargs)
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    image_thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)

    class Meta:
        verbose_name = "Imagem do Produto"
        verbose_name_plural = "Imagens dos Produtos"

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            img_original = Image.open(self.image)
            
            # Extraímos apenas o nome base para evitar caminhos duplicados
            nome_original = os.path.basename(self.image.name)
            nome_base = os.path.splitext(nome_original)[0]

            # 1. SALVA A IMAGEM PRINCIPAL (Redimensionada, mantendo proporção original)
            img_principal = img_original.copy()
            img_principal.thumbnail((2000, 2000), Image.Resampling.LANCZOS) # Exemplo: 1200px máx
            buffer_grande = BytesIO()
            img_principal.save(buffer_grande, format='WEBP', quality=90)
            self.image.save(f"{nome_base}.webp", ContentFile(buffer_grande.getvalue()), save=False)

            # 2. CRIA E SALVA O THUMBNAIL (600x600 proporcional)
            img_thumb = img_original.copy()
            img_thumb.thumbnail((600, 600), Image.Resampling.LANCZOS)
            buffer_pequeno = BytesIO()
            img_thumb.save(buffer_pequeno, format='WEBP', quality=85)
            
            # Aqui forçamos o caminho limpo no banco de dados
            nome_arquivo_thumb = f"{nome_base}_600.webp"
            self.image_thumbnail.name = os.path.join('products/thumbnails/', nome_arquivo_thumb)
            self.image_thumbnail.save(nome_arquivo_thumb, ContentFile(buffer_pequeno.getvalue()), save=False)

        super().save(*args, **kwargs)


DEFAULT_MARKDOWN = """| BR | CM |
| :---: | :---: |
| 34 | 22.8 |
| 35 | 23.5 |
| 40 | 26.8 |
| 44 | 29 |
"""

class SizeGuide(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='size_guides', verbose_name="Marca")
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='size_guides', verbose_name="Subcategoria")
    guide_text = models.TextField(
        verbose_name="Texto (Markdown)", 
        blank=True, 
        null=True, 
        default=DEFAULT_MARKDOWN,
        help_text="Monte sua tabela seguindo o modelo."
    )
    guide_image = models.ImageField(upload_to='size_guides/', blank=True, null=True, verbose_name="Imagem da Tabela")
    class Meta:
        verbose_name = "Guia de Medida"
        verbose_name_plural = "Guias de Medidas"
        # Garante apenas UMA tabela para a combinação exata de Marca + Subcategoria (ex: Vans + Camisetas)
        unique_together = ('brand', 'subcategory') 
    def __str__(self):
        return f"Tabela {self.brand.name} - {self.subcategory.name}"

@receiver(post_delete, sender=ProductImage)
@receiver(post_delete, sender=SizeGuide)
def delete_orphaned_image_files(sender, instance, **kwargs):
    """Garante a limpeza de arquivos físicos ao deletar instâncias do banco."""
    # Lista de campos de imagem possíveis dinamicamente
    fields_to_check = []
    
    if isinstance(instance, ProductImage):
        fields_to_check = [instance.image, instance.image_thumbnail]
    elif isinstance(instance, SizeGuide):
        fields_to_check = [instance.guide_image]

    for field in fields_to_check:
        if field and os.path.isfile(field.path):
            os.remove(field.path)
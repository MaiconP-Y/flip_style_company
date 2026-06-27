from django.db import models

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

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
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    color = models.ForeignKey(Color, on_delete=models.PROTECT, related_name='products')
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
        return f"[{self.brand.name}] {self.name} - {self.color.name}"

    @property
    def available_sizes(self):
        return list(
            self.variants.filter(stock__gt=0)
            .values_list('size__name', flat=True)
        )
    
    @property
    def preco_parcelado(self):
        return self.price / 12


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

    class Meta:
        verbose_name = "Variante de Produto"
        verbose_name_plural = "Variantes de Produtos"
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - Tam: {self.size.name} (Estoque: {self.stock})"
    
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

@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    for field in [instance.image, instance.image_thumbnail]:
        if field and os.path.isfile(field.path):
            os.remove(field.path)
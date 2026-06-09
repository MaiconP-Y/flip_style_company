from django.db import models

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

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

    class Meta:
        verbose_name = "Imagem do Produto"
        verbose_name_plural = "Imagens dos Produtos"

@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """
    Sinal que garante a limpeza do disco após a remoção do registro.
    Seguindo o padrão do 'post_delete' da documentação.
    """
    # Verificamos se o arquivo existe e o removemos
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)
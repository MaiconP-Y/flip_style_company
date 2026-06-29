from django.db import migrations
from django.utils.text import slugify

def popular_dados(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Subcategory = apps.get_model('products', 'Subcategory')
    Brand = apps.get_model('products', 'Brand')
    Size = apps.get_model('products', 'Size')
    Color = apps.get_model('products', 'Color')

    # 1. Cadastro de Categorias e Subcategorias
    estrutura_categorias = {
        "Roupas": ["Camisetas", "Calças", "Blusas", "Bermudas"],
        "Footwears": ["footwears"],
        "Área SKT": ["area-skt"],
    }

    for cat_name, sub_list in estrutura_categorias.items():
        category, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={'slug': slugify(cat_name)}
        )
        for sub_name in sub_list:
            Subcategory.objects.get_or_create(
                category=category,
                name=sub_name,
                defaults={'slug': slugify(sub_name)}
            )

    # 2. Cadastro de Marcas (Usando mapa para garantir slugs corretos)
    marcas_map = {
        "Avonts": "avonts",
        "Hocks": "hocks",
        "New": "new-skt",
        "Öus": "ous",
        "Thrasher": "thrasher",
        "Santa Cruz": "santa-cruz",
        "Tesla": "tesla",
        "Pixain": "pixain",
        "XXL": "xxl",
        "Mad Rats": "mad-rats",
        "Brothas": "brothas",
        "Stamp": "stamp"
    }

    for name, slug in marcas_map.items():
        Brand.objects.get_or_create(
            name=name,
            defaults={'slug': slug}
        )

    # 3. Cadastro de Tamanhos (Letras + Números)
    tamanhos_letras = ['PP', 'P', 'M', 'G', 'GG', 'XG', 'XGG', 'Unico']
    tamanhos_numeros = [str(n) for n in range(34, 51)]
    todos_tamanhos = tamanhos_letras + tamanhos_numeros

    for index, size_name in enumerate(todos_tamanhos):
        Size.objects.get_or_create(
            name=size_name,
            defaults={
                'slug': slugify(size_name),
                'order': index
            }
        )

    # 4. Cadastro de Cores Básicas
    cores_basicas = ["Preto", "Branco", "Cinza", "Marrom", "Bege", "Colorido", "Sem Cor"]
    
    for cor_name in cores_basicas:
        Color.objects.get_or_create(
            name=cor_name,
            defaults={'slug': slugify(cor_name)}
        )

def reverter_dados(apps, schema_editor):
    # Remove apenas o que foi criado por essa migração
    apps.get_model('products', 'Category').objects.all().delete()
    apps.get_model('products', 'Brand').objects.all().delete()
    apps.get_model('products', 'Size').objects.all().delete()
    apps.get_model('products', 'Color').objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        # IMPORTANTE: Verifique se o nome da migração anterior está correto aqui
        ('products', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(popular_dados, reverse_code=reverter_dados),
    ]
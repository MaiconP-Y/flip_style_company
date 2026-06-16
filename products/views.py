from django.shortcuts import render
from .models import Product

def home(request):
    # 1. Busca os produtos de destaque
    produtos_destaque = Product.objects.filter(
        is_featured=True, 
        variants__stock__gt=0
    ).distinct().prefetch_related('images')[:10]

    # 2. Definição da lista estática de categorias
    categorias = [
        {'name': 'Calça Cargo', 'image': 'img/categories/calca-cargo.webp'},
        {'name': 'Bermudas', 'image': 'img/categories/bermudas.webp'},
        {'name': 'Bonés', 'image': 'img/categories/bones.webp'},
        {'name': 'Calças', 'image': 'img/categories/calcas.webp'},
        {'name': 'Camisetas', 'image': 'img/categories/camisetas.webp'},
        {'name': 'Meias', 'image': 'img/categories/meias.webp'},
        {'name': 'Moletons', 'image': 'img/categories/moletons.webp'},
        {'name': 'Toucas', 'image': 'img/categories/toucas.webp'},
    ]

    marcas = [
        {'name': 'Avonts', 'image': 'img/brands/AVONTS.webp'},
        {'name': 'Hocks', 'image': 'img/brands/HOCKS.webp'},
        {'name': 'New', 'image': 'img/brands/NEW.webp'},
        {'name': 'Öus', 'image': 'img/brands/OUS.webp'},
        {'name': 'Santa Cruz', 'image': 'img/brands/SANTA_CRUZ.webp'},
        {'name': 'Tesla', 'image': 'img/brands/TESLA.webp'},
        {'name': 'Thrasher', 'image': 'img/brands/THRASHER.webp'},
    ]
    
    # Renderiza enviando os três conjuntos de dados
    return render(request, 'index.html', {
        'produtos': produtos_destaque,
        'categorias': categorias,
        'marcas': marcas # Enviando para o template
    })
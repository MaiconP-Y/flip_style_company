from django.db.models.functions import Lower
from .models import ProductModel

def modelos_menu(request):
    # Busca apenas os modelos que possuem produtos com alguma variante em estoque
    modelos_ativos = ProductModel.objects.filter(
        color_variants__variants__stock__gt=0
    ).distinct().order_by(Lower('name'))
    
    return {
        'modelos_do_menu': modelos_ativos
    }
from django.db.models.functions import Lower
from django.db.models import Q
from .models import ProductModel

def modelos_menu(request):
    modelos_ativos = ProductModel.objects.filter(
        color_variants__variants__stock__gt=0
    ).filter(
        Q(subcategory__category__slug='footwears') | Q(subcategory__slug='footwears')
    ).distinct().order_by(Lower('name'))
    
    return {
        'modelos_do_menu': modelos_ativos
    }
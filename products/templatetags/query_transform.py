from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Retorna os parâmetros de URL atuais modificados pelos novos argumentos.
    Uso: {% query_transform cor=c.slug %}
    """
    request = context['request']
    updated = request.GET.copy()
    
    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, None) # Permite remover um filtro se passar None
            
    return updated.urlencode()
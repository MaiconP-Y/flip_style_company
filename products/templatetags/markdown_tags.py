from django import template
import markdown as md

register = template.Library()

@register.filter(name='markdown')
def markdown_filter(text):
    # O 'tables' ativa o suporte a tabelas nativas do Markdown
    return md.markdown(text, extensions=['tables'])
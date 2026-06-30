from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from products.views import home, ProductsListView, QuemSomosView, politica_privacidade, ProductDetailView

urlpatterns = [
    path('c-cyber-control/', admin.site.urls),
    path('', home, name='home'),
    path('quem_somos/', QuemSomosView, name='quem_somos'),
    path('politica-de-privacidade/', politica_privacidade, name='privacidade'),
    path('produtos/', ProductsListView.as_view(), name='products'),
    path('produtos/categoria/<slug:category_slug>/', ProductsListView.as_view(), name='category'),
    path('produtos/sub/<slug:subcategory_slug>/', ProductsListView.as_view(), name='subcategory'),
    path('produto/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]

# Apenas adicione as rotas de mídia se estivermos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
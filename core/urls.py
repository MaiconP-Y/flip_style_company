from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView

from accounts.views import login_view, logout_view
from products.views import (
    ProductDetailView,
    ProductsListView,
    PrivacidadeView,
    QuemSomosView,
    home,
)
from promissorias.views import (
    painel_promissorias,
    whatsapp_qrcode,
    whatsapp_status,
    clientes_promissorias,
)

urlpatterns = [
    path("c-cyber-control/", admin.site.urls),
    path("accounts/login/", login_view, name="login"),
    path("accounts/logout/", logout_view, name="logout"),
    path("", home, name="home"),
    path("quem_somos/", QuemSomosView, name="quem_somos"),
    path("politica-de-privacidade/", PrivacidadeView, name="privacidade"),
    path("produtos/", ProductsListView.as_view(), name="products"),
    path("produtos/categoria/<slug:category_slug>/", ProductsListView.as_view(), name="category"),
    path("produtos/sub/<slug:subcategory_slug>/", ProductsListView.as_view(), name="subcategory"),
    path("produto/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path("promissorias/", painel_promissorias, name="painel_promissorias"),
    path("clientes/", clientes_promissorias, name="clientes"),
    path("whatsapp/qrcode/", whatsapp_qrcode, name="whatsapp_qrcode"),
    path("whatsapp/status/", whatsapp_status, name="whatsapp_status"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "img/favicon.ico", permanent=True),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
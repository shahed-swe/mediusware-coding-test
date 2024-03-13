from django.urls import path
from django.views.generic import TemplateView

from product.views.product import (
    CreateProductView,
    ProductListView,
    CreateProductApiView,
    UpdateProductView,
    ProductDetailView,
)
from product.views.variant import VariantView, VariantCreateView, VariantEditView

app_name = "product"

urlpatterns = [
    # Variants URLs
    path("variants/", VariantView.as_view(), name="variants"),
    path("variant/create", VariantCreateView.as_view(), name="create.variant"),
    path("variant/<int:id>/edit", VariantEditView.as_view(), name="update.variant"),
    # Products URLs
    path("create/", CreateProductView.as_view(), name="create.product"),
    path("list/", ProductListView.as_view(), name="list.product"),
    path(
        "api/create_product/", CreateProductApiView.as_view(), name="create_product_api"
    ),
    path("update/<int:id>/", UpdateProductView.as_view(), name="update.product"),
    path(
        "api/update/<int:product_id>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),
]

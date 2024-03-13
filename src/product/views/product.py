from django.views import generic
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger

from django.views.generic import ListView
from django.db.models import Prefetch
from product.models import *

class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context


class ProductListView(ListView):
    model = Product
    template_name = (
        "products/list.html" 
    )
    context_object_name = "products"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.all()
        product_variant_prices = ProductVariantPrice.objects.filter(
            product__in=products
        )

        product_prices_dict = {}
        for price in product_variant_prices:
            if price.product_id not in product_prices_dict:
                product_prices_dict[price.product_id] = []
            product_prices_dict[price.product_id].append(price)

        for product in products:
            product.product_variant_prices = product_prices_dict.get(product.id, [])

        


        context["products"] = products
        context["page_obj"] = context['page_obj'] 
        return context

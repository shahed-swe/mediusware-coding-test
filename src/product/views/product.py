from django.views import generic
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger

from django.views.generic import ListView
from django.db.models import Prefetch, Q
from product.models import *
from product.serializers import ProductSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

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

    # to get product details properly
    def get_product_details(self,products):
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
        return products

    # to filter things here
    def filter_products(self,context):
        queryset = super().get_queryset()

        title_filter = self.request.GET.get("title")
        variant_filter = self.request.GET.get("variant")
        min_price_filter = self.request.GET.get("price_from")
        max_price_filter = self.request.GET.get("price_to")
        date_filter = self.request.GET.get("date")

        if title_filter != None:
            queryset = queryset.filter(title__icontains=title_filter)

        if variant_filter:
            queryset = queryset.filter(
                Q(
                    productvariantprice__product_variant_one__variant_title__icontains=variant_filter
                )
                | Q(
                    productvariantprice__product_variant_two__variant_title__icontains=variant_filter
                )
                | Q(
                    productvariantprice__product_variant_three__variant_title__icontains=variant_filter
                )
            )

        if min_price_filter:
            queryset = queryset.filter(
                productvariantprice__price__gte=min_price_filter
            )

        if max_price_filter:
            queryset = queryset.filter(
                productvariantprice__price__lte=max_price_filter
            )

        if date_filter:
            queryset = queryset.filter(created_at=date_filter)

        context["title_filter"] = title_filter or ""
        context["variant_filter"] = variant_filter or ""
        context["min_price_filter"] = min_price_filter or ""
        context["max_price_filter"] = max_price_filter or ""
        context["date_filter"] = date_filter or ""

        return queryset,context

    def get_dynamic_variants(self):
        root_variants = Variant.objects.all()
        for variant in root_variants:
            product_variants = ProductVariant.objects.filter(variant = variant.pk).values("variant_title").distinct()
            variant.productvariants = product_variants
        return root_variants

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # product showing mechanism
        products = Product.objects.all()

        # filter products based on title, price range, variant and date
        products, context = self.filter_products(context)

        paginator = Paginator(products, self.paginate_by)
        page = self.request.GET.get("page")

        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        products = self.get_product_details(products)

        variants = self.get_dynamic_variants()

        context["products"] = products
        context["page_obj"] = context['page_obj'] 
        context["variants"] = variants

        return context


@method_decorator(csrf_exempt, name="dispatch")
class CreateProductApiView(APIView):

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser,)

    def get_variant_id(self,serializer, input_tag):
        main_vars = serializer.validated_data["variants"]
        tag_to_option_mapping = {}
        for variant in main_vars:
            option = variant["option"]
            tags = variant["tags"]
            for tag in tags:
                tag_to_option_mapping[tag] = option

        # Retrieve the option for the specified tag
        option_for_tag = tag_to_option_mapping.get(input_tag)
        return option_for_tag

    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = Product.objects.filter(sku=serializer.validated_data["sku"]).first()
            if product:
                return Response({"message": "Product SKU is NON-Unique"})

            product = Product.objects.create(
                title=serializer.validated_data["name"],
                sku=serializer.validated_data["sku"],
                description=serializer.validated_data["description"],
                # Add additional fields as needed
            )

            allvars_with_price = serializer.validated_data["variantPrices"]
            try:
                for variants in allvars_with_price:
                    title = variants['title']
                    title_part = title.split("/")
                    created_variants = []
                    for var_title in title_part:

                        product_variant = ProductVariant.objects.filter(variant_title=var_title).first()
                        if not product_variant:
                            if var_title != "":
                                variant_id = self.get_variant_id(serializer, var_title)
                                variant = Variant.objects.get(pk=variant_id)
                                if variant != None:
                                    product_variant = ProductVariant.objects.create(
                                        variant_title=var_title,
                                        variant=variant,
                                        product=product,
                                    )
                        created_variants.append(product_variant)
                    product_variant_price = ProductVariantPrice(
                        price = variants['price'],
                        stock = variants['stock'],
                        product=product
                    )
                    if created_variants[0] is not None:
                        product_variant_price.product_variant_one = created_variants[0]
                    if created_variants[1] is not None:
                        product_variant_price.product_variant_two = created_variants[1]
                    if created_variants[2] is not None:
                        product_variant_price.product_variant_three = created_variants[2]

                    product_variant_price.save()

            except Exception as e:
                raise APIException(detail="Internal Server Error", code=500)
            return Response({"message": "Data successfully processed"})

        # Return an error response for invalid data
        return Response({"error": serializer.errors}, status=400)

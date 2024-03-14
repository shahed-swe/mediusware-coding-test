from django.views import generic
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger

from django.views.generic import ListView
from django.db.models import Prefetch, Q
from product.models import *
from product.serializers import ProductSerializer, ProductDetailSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException
from django.db import transaction


class CreateProductView(generic.TemplateView):
    template_name = 'products/create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values('id', 'title')
        context['product'] = True
        context['variants'] = list(variants.all())
        return context


class UpdateProductView(generic.TemplateView):
    template_name = "products/update.html"

    def get_context_data(self, **kwargs):
        context = super(UpdateProductView, self).get_context_data(**kwargs)
        variants = Variant.objects.filter(active=True).values("id", "title")
        context["product"] = True
        context["variants"] = list(variants.all())
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

        option_for_tag = tag_to_option_mapping.get(input_tag)
        return option_for_tag

    def create_product(self, serializer):
        product = Product.objects.filter(sku=serializer.validated_data["sku"]).first()
        if product:
            return Response({"message": "Product SKU is NON-Unique"})

        product = Product.objects.create(
            title=serializer.validated_data["name"],
            sku=serializer.validated_data["sku"],
            description=serializer.validated_data["description"],
        )

        allvars_with_price = serializer.validated_data["variantPrices"]
        variants = serializer.validated_data["variants"]

        # saving variant
        variant_mapping = {}
        for variant in variants:
            option = variant['option']
            tags = variant['tags']
            for tag in tags:
                # Ensure Variant exists
                variant_obj = Variant.objects.get(pk=option)
                # Ensure ProductVariant exists
                product_variant = ProductVariant.objects.create(
                    variant_title=f"{tag}",
                    variant=variant_obj,
                    product=product
                )
                variant_mapping[f"{option}-{tag}"] = product_variant

        for variant_price in allvars_with_price:
            title = variant_price['title']
            price = variant_price['price']
            stock = variant_price['stock']
            # Split the title to get variant tags, assuming format "size/color/"
            tags = title.split('/')[:-1]  # Remove the last empty item due to trailing '/'

            # Map tags to ProductVariant instances
            product_variants = [variant_mapping.get(f"{idx+1}-{tag}") for idx, tag in enumerate(tags)]

            ProductVariantPrice.objects.create(
                product_variant_one=product_variants[0] if len(product_variants) > 0 else None,
                product_variant_two=product_variants[1] if len(product_variants) > 1 else None,
                product_variant_three=product_variants[2] if len(product_variants) > 2 else None,
                price=price,
                stock=stock,
                product=product
            )

    @transaction.atomic
    def update_product(self, serializer):
        product = Product.objects.get(pk=serializer.validated_data["id"])
        product.title = serializer.validated_data["name"]
        product.sku = serializer.validated_data["sku"]
        product.description = serializer.validated_data["description"]
        product.save()

        allvars_with_price = serializer.validated_data["variantPrices"]
        variants = serializer.validated_data["variants"]
        try:
            variant_mapping = {}
            for variant in variants:
                option = variant['option']
                tags = variant['tags']
                for tag in tags:
                    variant_obj, created = Variant.objects.get_or_create(title=tag)
                    product_variant, created = ProductVariant.objects.get_or_create(
                        variant=variant_obj, 
                        product=product,
                        defaults={'variant_title': f"{tag}"}
                    )
                    if not created:
                        # Update logic here if needed
                        pass
                    variant_mapping[f"{option}-{tag}"] = product_variant

            for variant_price in allvars_with_price:
                title = variant_price['title']
                price = variant_price['price']
                stock = variant_price['stock']
                tags = title.split('/')[:-1]  

                product_variants = [variant_mapping.get(f"{idx+1}-{tag}") for idx, tag in enumerate(tags)]
                _, created = ProductVariantPrice.objects.update_or_create(
                    product=product,
                    product_variant_one=product_variants[0] if len(product_variants) > 0 else None,
                    product_variant_two=product_variants[1] if len(product_variants) > 1 else None,
                    product_variant_three=product_variants[2] if len(product_variants) > 2 else None,
                    defaults={'price': price, 'stock': stock}
                )
                if not created:
                    pass
        except Exception as e:
            raise APIException(detail=e, code=500)

    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product_id = serializer.validated_data.get("id", None)
            if product_id:
                self.update_product(serializer)
            else:
                self.create_product(serializer)

            return Response({"message": "Data successfully processed"})

        # Return an error response for invalid data
        return Response({"error": serializer.errors}, status=400)


class ProductDetailView(APIView):

    def get(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(pk=product_id)

            serializer = ProductDetailSerializer(product)

            return Response(serializer.data)

        except Product.DoesNotExist:
            return Response(
                {"error": f"Product with id {product_id} does not exist"}, status=404
            )
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": "Internal Server Error"}, status=500)

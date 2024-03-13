# serializers.py
from rest_framework import serializers
import json


class JSONStringField(serializers.Field):
    def to_internal_value(self, data):
        try:
            # If it's a string, attempt to parse it as JSON
            if isinstance(data, str):
                return json.loads(data)
            # If it's already a Python object, return it unchanged
            elif isinstance(data, (list, dict)):
                return data
            # If it's neither a string nor a Python object, raise an error
            else:
                raise serializers.ValidationError(
                    "Invalid input. Must be a stringified JSON or a JSON object."
                )
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format.")


class ProductSerializer(serializers.Serializer):
    name = serializers.CharField()
    sku = serializers.CharField()
    description = serializers.CharField()
    variants = JSONStringField()
    variantPrices = JSONStringField()
    media = serializers.ListField(child=serializers.FileField(), required=False)

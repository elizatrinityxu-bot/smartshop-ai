from rest_framework import serializers
from product_recommendations.models import Product, Recommendation


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'category',
            'description',
            'price',
            'stock',
            'is_active',
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            'product',
            'score',
            'generated_by',
            'created_at'
        ]

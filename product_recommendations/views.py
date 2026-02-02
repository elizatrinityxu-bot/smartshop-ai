
from rest_framework.decorators import api_view

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from product_recommendations.models import UserInteraction, Recommendation, Product
from product_recommendations.serializers import RecommendationSerializer, ProductSerializer
from product_recommendations.services.ai_recommendation_service import (
    generate_recommendations_for_user
)

def index(request):
    return HttpResponse("SmartShop Recommendation API is running")


@api_view(["GET"])
def product_list(request):
    products = Product.objects.filter(is_active=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


class UserRecommendationAPIView(APIView):
    """
    Returns AI-generated product recommendations for a given user
    """

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        interactions = UserInteraction.objects.filter(user=user)

        # Call AI recommendation engine
        products = generate_recommendations_for_user(user, interactions)

        # Store/update recommendations
        recommendations = []
        for product in products:
            rec, _ = Recommendation.objects.update_or_create(
                user=user,
                product=product,
                defaults={
                    "score": 0.9,
                    "generated_by": "AI Recommendation Engine"
                }
            )
            recommendations.append(rec)

        serializer = RecommendationSerializer(recommendations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@login_required
def recommendation_dashboard(request):
    # Allow staff to view recommendations for any user via ?user_id=<id>
    users = User.objects.all().order_by('username')

    selected_user = request.user
    selected_user_id = request.GET.get('user_id')
    if selected_user_id and request.user.is_staff:
        try:
            selected_user = User.objects.get(id=selected_user_id)
        except User.DoesNotExist:
            selected_user = request.user

    interactions = UserInteraction.objects.filter(user=selected_user)
    recommendations = generate_recommendations_for_user(selected_user, interactions)

    # Add simulated AI score
    recommendations_with_score = [
        {
            "product": product,
            "score": round(1 - index * 0.1, 2)
        }
        for index, product in enumerate(recommendations)
    ]

    return render(request, "recommendations/dashboard.html", {
        "user": request.user,
        "selected_user": selected_user,
        "users": users,
        "recommendations": recommendations_with_score
    })

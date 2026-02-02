from django.urls import path
from .views import product_list

from product_recommendations.views import (
    index,
    UserRecommendationAPIView,
    recommendation_dashboard
)

urlpatterns = [
    # Health check
    path('api/recommendations/', index, name='api-health-check'),

    # REST API
    path(
        'api/recommendations/<int:user_id>/',
        UserRecommendationAPIView.as_view(),
        name='user-recommendations'
    ),
    path(
        'api/recommendations/products/',
        product_list,
        name='product-list'
    ),
    
    path("products/", product_list, name="product-list"),
  
    # UI page
    path(
        'recommendations/dashboard/',
        recommendation_dashboard,
        name='recommendation-dashboard'
    ),  
       
]

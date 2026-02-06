from django import views
from django.urls import path
from . import views
from .views import product_list, smart_search_view, product_detail, submit_review, products_page, autocomplete_search
from .views import chatbot_api

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
    
  
    # UI page
    path(
        'recommendations/dashboard/',
        recommendation_dashboard,
        name='recommendation-dashboard'
    ),
    
    # existing urls here
    path("search/", smart_search_view, name="smart_search"),
    
    # Product detail and review submission
    path("products/", products_page, name="products_page"),
    path("products/<int:product_id>/", product_detail, name="product_detail"),
    path("products/<int:product_id>/submit_review/", submit_review, name="submit_review"),
    
    # Chatbot API endpoint
    path("chatbot/",views.chatbot_api,name="chatbot_api"),
    
    # Chatbot greeting endpoint
    path("chatbot/greeting/", views.chatbot_greeting, name="chatbot_greeting"),
    
    # Autocomplete search endpoint
    path("search/autocomplete/", autocomplete_search, name="autocomplete_search"),
    
]

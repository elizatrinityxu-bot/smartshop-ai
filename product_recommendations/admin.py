from django.contrib import admin
from product_recommendations.models import (
    Category,
    Product,
    UserProfile,
    UserInteraction,
    Order,
    OrderItem,
    Recommendation,
    Review
)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(UserProfile)
admin.site.register(UserInteraction)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Recommendation)
admin.site.register(Review)

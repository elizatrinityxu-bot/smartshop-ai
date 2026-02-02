from django.db import models
from django.contrib.auth.models import User


# -----------------------------
# 3.1 User & Profile Models
# -----------------------------

class UserProfile(models.Model):
    """
    Extends Django's built-in User model to store demographic
    and preference-related features used for recommendation inference.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username


# -----------------------------
# 3.2 Product & Category Models
# -----------------------------

class Category(models.Model):
    """
    Represents product categories for classification and filtering.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents products available in the system.
    """
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# -----------------------------
# 3.3 User Interaction Model
# -----------------------------

class UserInteraction(models.Model):
    """
    Captures user behavior signals that drive recommendation logic.
    """

    INTERACTION_CHOICES = (
        ('view', 'View'),
        ('click', 'Click'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase', 'Purchase'),
        ('like', 'Like'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_CHOICES
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} - {self.product.name}"


# -----------------------------
# 3.4 Order & Purchase History Models
# -----------------------------

class Order(models.Model):
    """
    Represents a completed or in-progress order by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    """
    Represents individual products within an order.
    """
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# -----------------------------
# 3.5 Recommendation Output Model
# -----------------------------

class Recommendation(models.Model):
    """
    Stores AI-generated product recommendations for users.
    Used for caching and analytics to avoid repeated AI calls.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField()
    generated_by = models.CharField(
        max_length=50,
        default="Gemini AI"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} → {self.product.name} ({self.score})"

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# -----------------------------
#   User & Profile Models
# -----------------------------

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Personalisation fields
    preferred_categories = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated list of preferred categories"
    )
    budget_level = models.CharField(
        max_length=50,
        help_text="Budget preference: low / medium / high"
    )
    tone_preference = models.CharField(
        max_length=50,
        help_text="Tone preference: friendly / practical / stylish / performance"
    )
    usage_context = models.CharField(
        max_length=255,
        help_text="Usage context such as gym, home, office"
    )

    def __str__(self):
        return self.user.username



# -----------------------------
#   Product & Category Models
# -----------------------------

class Category(models.Model):
    """
    Represents product categories for classification and filtering.
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents products available in the system.
    """
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Short UI description (optional)
    description = models.TextField(blank=True)

    # Layer 1: Base description for AI grounding (required)
    base_description = models.TextField()
    
    # Layer 2: AI-generated product description (cached)
    ai_description = models.TextField(blank=True, null=True)
    
    # Inventory & visibility
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Product attributes for AI grounding
    brand = models.CharField(max_length=100, blank=True, null=True)
    material = models.CharField(max_length=255, blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    use_case = models.CharField(max_length=255, blank=True, null=True)
    care_instructions = models.TextField(blank=True, null=True)

    # Product image
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name



# -----------------------------
#   User Interaction Model
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
#   Order & Purchase History Models
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
#   Recommendation Output Model
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


# -----------------------------
#   Review Model
# -----------------------------


class Review(models.Model):
    """
    Stores customer reviews for products.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField(
    validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  
        
    review_text = models.TextField()

    # AI-generated fields (cached)
    sentiment_label = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    ai_summary_cache = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_summarized_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.rating}★"


# -----------------------------
#   ChatMessage Model
# -----------------------------

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message[:30]}"
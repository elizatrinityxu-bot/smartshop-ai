
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from product_recommendations.models import Review, UserInteraction, Recommendation, Product, ChatMessage, Category
from product_recommendations.services.smart_search_service import smart_search_products
from product_recommendations.serializers import RecommendationSerializer, ProductSerializer
from product_recommendations.services.ai_recommendation_service import (
    generate_recommendations_for_user
)
from product_recommendations.services.review_summary_service import (
    get_or_generate_review_summary
)

import json
from product_recommendations.services.ai_recommendation_service import client
from django.contrib.auth import logout
from product_recommendations.services.product_description_service import get_or_generate_product_description
from .models import ChatMessage


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

def autocomplete_search(request):
    q = request.GET.get("q", "").strip()
    suggestions = []

    if len(q) >= 2:
        # Product name suggestions
        product_names = Product.objects.filter(
            is_active=True,
            name__icontains=q
        ).values_list("name", flat=True)[:5]

        # Category suggestions
        category_names = Category.objects.filter(
            name__icontains=q
        ).values_list("name", flat=True)[:5]

        suggestions = list(product_names) + list(category_names)

    return JsonResponse({"suggestions": suggestions})


@login_required
def recommendation_dashboard(request):
    # Allow staff to view recommendations for any user via ?user_id=<id>
    users = User.objects.all().order_by('username') if request.user.is_staff else None

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
        "selected_user": selected_user,
        "users": users,
        "recommendations": recommendations_with_score
    })

def smart_search_view(request):
    """
    Smart Search endpoint.
    Accepts query via GET parameter ?q=
    Returns list of matching products plus parsed metadata for UI transparency.
    """

    query = request.GET.get("q", "").strip()

    products, meta = smart_search_products(query, return_metadata=True)

    results = []
    for product in products:
        results.append({
            "id": product.id,
            "name": product.name,
            "category": product.category.name,
            "price": float(product.price),
            "brand": product.brand,
            "image_url": product.image_url,
            "use_case": product.use_case,
        })

    return JsonResponse({
        "query": query,
        "count": len(results),
        "results": results,
        "parsed": meta.get("parsed"),
        "applied_filters": meta.get("applied_filters"),
    })
    
@login_required
def submit_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)

        rating = request.POST.get("rating")
        review_text = request.POST.get("review_text", "").strip()

        if rating and review_text:
            review = Review.objects.create(
                product=product,
                user=request.user,
                rating=int(rating),
                review_text=review_text
            )

            # 🔁 Invalidate AI cache so the summary is regenerated
            review.ai_summary_cache = None
            review.sentiment_label = None
            review.last_summarized_at = None
            review.save()

        # Redirect back to product detail page after submission
        return redirect('product_detail', product_id=product.id)
    # For other methods, redirect back to product page
    return redirect('product_detail', product_id=product_id)

@login_required    
def products_page(request):
    """Public product listing UI (non-authenticated users allowed)."""
    products = Product.objects.filter(is_active=True)
    return render(request, "products/product_list.html", {"products": products})


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    ai_desc =  get_or_generate_product_description(product)
    
    review_summary = get_or_generate_review_summary(product)

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "review_summary": review_summary,
            "ai_description": ai_desc,
        }
    )
    

@login_required
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_message = data.get("message", "")
    msg = user_message.lower().strip()
    
    # Determine if message is a follow-up about availability or reviews
    AVAILABILITY_INTENTS = ["stock", "in stock", "available", "availability"]
    REVIEW_INTENTS = ["review", "reviews", "rating", "good", "bad", "feedback", "worth"]

    # Check for follow-up intents
    is_followup = any(k in msg for k in (AVAILABILITY_INTENTS + REVIEW_INTENTS))

    # Check last message for product context if follow-up
    last_product = None
    if is_followup:
        last_message = (
            ChatMessage.objects
            .filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if last_message and last_message.response:
            # Try multiple patterns to extract product name
            import re
            
            # Pattern 1: **ProductName** (bold)
            match = re.search(r'\*\*([^*]+)\*\*', last_message.response)
            
            # Pattern 2: "ProductName ($" (product with price)
            if not match:
                match = re.search(r':\s*([^(]+?)\s*\(\$', last_message.response)
            
            # Pattern 3: Just search the response text against all products
            if match:
                product_name = match.group(1).strip()
                try:
                    last_product = Product.objects.get(
                        name__iexact=product_name,
                        is_active=True
                    )
                except Product.DoesNotExist:
                    last_product = Product.objects.filter(
                        name__icontains=product_name,
                        is_active=True
                    ).first()
            else:
                # Fallback: search all active products and see which one appears in response
                all_products = Product.objects.filter(is_active=True)
                for p in all_products:
                    if p.name in last_message.response:
                        last_product = p
                        break

    
    # Greeting intent
    if msg in ["hi", "hello", "hey", "good morning", "good afternoon"]:
        reply = (
            f"Hi {request.user.first_name or request.user.username}! 👋 "
            "How can I help you today?"
        )
        ChatMessage.objects.create(
            user=request.user, message=user_message, response=reply
        )
        return JsonResponse({"reply": reply})
    
    # ---- Primary: smart search for products ----
    products = []
    meta = {"parsed": {}, "applied_filters": {}}
    
    if not is_followup or not last_product:     
        # Use smart search with metadata to get parsed filters and price info
        products, meta = smart_search_products(user_message, user=request.user, return_metadata=True)
    
        # Prefer exact keyword matches for concrete product nouns
        if products:
            tokens = [w for w in msg.split() if w not in ["i", "need", "want", "a", "an", "the"]]

            explicit_matches = [
                p for p in products
                if any(token in p.name.lower() for token in tokens)
            ]            
            if explicit_matches:
                products = explicit_matches    
    
        products = list(products)[:1] # IMPORTANT: only 1 product for clarity

    product = last_product if (is_followup and last_product) else (products[0] if products else None)   
            
    
    # If no products found, try to reference last chat message for context
    if not product and not is_followup:
        last_chat = (
            ChatMessage.objects
            .filter(user=request.user)
            .order_by("-created_at")
            .first()
        )

        if last_chat and last_chat.response:
            # Extract product name from previous response
            import re
            match = re.search(r'\*\*([^*]+)\*\*', last_chat.response)
            if not match:
                match = re.search(r':\s*([^(]+?)\s*\(\$', last_chat.response)
            
            if match:
                product_name = match.group(1).strip()
                try:
                    product = Product.objects.get(
                        name__iexact=product_name,
                        is_active=True
                    )
                except Product.DoesNotExist:
                    product = Product.objects.filter(
                        name__icontains=product_name,
                        is_active=True
                    ).first()
            else:
                # Fallback search
                all_products = Product.objects.filter(is_active=True)
                for p in all_products:
                    if p.name in last_chat.response:
                        product = p
                        break
    
    if not product and len(products) > 1 and any(k in msg for k in AVAILABILITY_INTENTS + REVIEW_INTENTS):
        reply = (
            "I found a few matching products. "
            "Could you tell me which one you're referring to?"
        )
        ChatMessage.objects.create(
            user=request.user, message=user_message, response=reply
        )
        return JsonResponse({"reply": reply})

     
    # Handle availability requests  
    if product and any(k in msg for k in AVAILABILITY_INTENTS):
        if product.stock > 0:
            reply = f"Yes, **{product.name}** is currently in stock."
        else:
            reply = f"Sorry, **{product.name}** is currently out of stock."

        ChatMessage.objects.create(
            user=request.user, message=user_message, response=reply
        )
        return JsonResponse({"reply": reply})
         

    # Handle review-related questions
    if product and any(k in msg for k in REVIEW_INTENTS):
        from product_recommendations.models import Review
        from django.db.models import Avg, Count

        reviews = Review.objects.filter(product=product)

        if not reviews.exists():
            reply = f"There are no customer reviews yet for **{product.name}**."
        else:
            # Use cached AI summaries if available
            ai_summaries = reviews.exclude(ai_summary_cache__isnull=True)\
                                .exclude(ai_summary_cache__exact="")\
                                .values_list("ai_summary_cache", flat=True)

            sentiments = reviews.exclude(sentiment_label__isnull=True)\
                                .values_list("sentiment_label", flat=True)

            avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
            total_reviews = reviews.count()

            if ai_summaries:
                # Combine cached AI summaries (lightweight + deterministic)
                combined_summary = " ".join(set(ai_summaries))

                # Sentiment distribution
                sentiment_counts = {}
                for s in sentiments:
                    sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

                dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)

                reply = (
                    f"Here’s what customers say about **{product.name}**:\n\n"
                    f"**AI Summary:** {combined_summary}\n\n"
                    f"**Overall Sentiment:** {dominant_sentiment}\n"
                    f"**Average Rating:** {avg_rating:.1f}/5 "
                    f"from {total_reviews} reviews"
                )
            else:
                # Fallback: no AI summary yet, but reviews exist
                reply = (
                    f"**{product.name}** has {total_reviews} reviews "
                    f"with an average rating of {avg_rating:.1f}/5.\n\n"
                    "Detailed AI summaries will be available soon."
                )

        ChatMessage.objects.create(
            user=request.user,
            message=user_message,
            response=reply
        )
        return JsonResponse({"reply": reply})
  

    # Build reply based on search results
    if products:
        max_price = meta.get('parsed', {}).get('max_price')
        price_relaxed = meta.get('applied_filters', {}).get('price_relaxed', False)
        
        # Build product list with pricing info
        product_lines = []
        for p in products:
            line = p.name
            price = float(p.price)
            line += f" (${price:.2f})"
            
            # Add price-relative warning based on how much it exceeds budget
            if max_price and price > max_price:
                overage_pct = ((price - max_price) / max_price) * 100
                if overage_pct <= 10:
                    indicator = "⚠️ slightly above"
                elif overage_pct <= 25:
                    indicator = "⚠️ moderately above"
                else:
                    indicator = "⚠️ well above"
                line += f" {indicator} your ${max_price:.0f} budget"
            
            product_lines.append(line)
        
        reply = "Here's what I found for you: " + ", ".join(product_lines)
        
        # Add note if price constraint was relaxed
        if price_relaxed and max_price:
            reply += f"\n(Note: No items strictly under ${max_price:.0f} found, showing alternatives)"
    else:
        parsed = meta.get("parsed", {}) or {}
        category = parsed.get("mapped_category") or parsed.get("category")
        keywords = parsed.get("keywords", [])

        reply = "I don't currently have a matching item in the SmartShop catalogue."

        if category:
            reply += f" I detected a request related to **{category}**."

            category_exists = Product.objects.filter(
                is_active=True,
                category__name__icontains=category
            ).exists()

            if category_exists:
                reply += (
                    f" While I don't have that specific item, you can browse other products "
                    f"available under **{category}**."
                )
            else:
                reply += f" At the moment, there are no products listed under **{category}**."

        if keywords:
            reply += f" (Keywords detected: {', '.join(keywords)}.)"

        reply += " You can browse **All Products** or try a more specific search."

    # Persist chat message
    ChatMessage.objects.create(user=request.user, message=user_message, response=reply)

    return JsonResponse({"reply": reply})


# Separate greeting endpoint (if your frontend calls this on chatbot open)
@login_required
def chatbot_greeting(request):
    """Return initial greeting when chatbot is opened"""
    user_name = request.user.first_name or request.user.username
    greeting = f"Hi {user_name}! 👋 How can I help you today?"
    return JsonResponse({"reply": greeting})  # Changed from "greeting" to "reply"


def logout_view(request):
    logout(request)
    return redirect('login')
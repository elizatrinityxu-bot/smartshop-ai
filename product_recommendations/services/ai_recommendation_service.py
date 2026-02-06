import os
from dotenv import load_dotenv
from openai import OpenAI
import re
from product_recommendations.models import Product
from product_recommendations.models import UserProfile

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def personalize_score(base_score, product, user_profile):
    score = base_score

    if user_profile:
        # Category preference
        if user_profile.preferred_categories:
            preferred = [
                c.strip().lower()
                for c in user_profile.preferred_categories.split(",")
            ]
            if product.category.name.lower() in preferred:
                score += 0.3

        # Usage context
        if user_profile.usage_context and product.use_case:
            if user_profile.usage_context.lower() in product.use_case.lower():
                score += 0.2

        # Budget sensitivity
        if user_profile.budget_level == "low" and product.price <= 60:
            score += 0.1
        elif user_profile.budget_level == "medium" and 60 < product.price <= 150:
            score += 0.1
        elif user_profile.budget_level == "high" and product.price > 150:
            score += 0.1

    return round(score, 2)


def generate_recommendations_for_user(user, interactions):
    interaction_summary = []

    for interaction in interactions:
        interaction_summary.append(
            f"{interaction.interaction_type} -> {interaction.product.name}"
        )

    products = Product.objects.filter(is_active=True)
    product_names = [p.name for p in products]

    prompt = f"""
You are a product recommendation engine.

User behavior:
{", ".join(interaction_summary)}

Available products:
{", ".join(product_names)}

Recommend a ranked list of products the user is most likely to purchase.
Return only a comma-separated list of product names.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI recommendation engine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
    except Exception as e:
        print("OpenAI API error:", e)
        return Product.objects.none()

    # Safely extract content from the chat response
    content = ""
    if response.choices and getattr(response.choices[0].message, "content", None):
        content = response.choices[0].message.content

    # Split by comma and strip numbering like '1.' or '1)'
    recommended_names = [
        re.sub(r'^\s*\d+[\.|\)]\s*', '', name).strip()
        for name in content.split(",")
        if name.strip()
    ]

    # Fetch user profile
    user_profile = UserProfile.objects.filter(user=user).first()

    # Preserve AI ordering by mapping name -> rank
    ai_rank = {name: idx for idx, name in enumerate(recommended_names)}

    recommended_products = (
        products
        .filter(name__in=recommended_names)
    )

    scored_products = []

    for product in recommended_products:
        base_score = 1.0 - (ai_rank.get(product.name, 0) * 0.05)

        final_score = personalize_score(
            base_score=base_score,
            product=product,
            user_profile=user_profile
        )

        scored_products.append((product, final_score))

    # Sort by personalized score
    scored_products.sort(key=lambda x: x[1], reverse=True)

    # Return ordered products (you may also return scores if needed)
    return [p[0] for p in scored_products]




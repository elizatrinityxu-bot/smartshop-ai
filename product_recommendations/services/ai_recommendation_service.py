import os
from dotenv import load_dotenv
from openai import OpenAI
import re
from product_recommendations.models import Product

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

    return products.filter(name__in=recommended_names)



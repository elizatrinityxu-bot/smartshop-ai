
"""
DEPRECATED / NOT IN ACTIVE USE

This module was part of an earlier chatbot prototype.
Chatbot logic has since been consolidated into `chatbot_api`
inside `views.py`, which reuses `smart_search_products`
for consistent intent parsing and filtering.

This file is retained for reference only and is not used
by the current application flow.
"""

from openai import OpenAI
from product_recommendations.models import Product
from product_recommendations.services.smart_search_service import smart_search_products


client = OpenAI()

def handle_chat_message(user, message):
    print("🔥 NEW CHATBOT LOGIC EXECUTED 🔥")
    
    products, meta = smart_search_products(
        message,
        user=user,
        return_metadata=True
    )

    parsed = meta.get("parsed", {}) or {}
    applied = meta.get("applied_filters", {}) or {}

    # Case 1: No products found → category-aware, data-driven response
    if not products:
        category = parsed.get("mapped_category") or parsed.get("category")
        keywords = parsed.get("keywords", [])

        explanation = "I don’t currently have a matching item in the SmartShop catalogue."

        if category:
            explanation += f" I detected a request related to **{category}**."

            # Check if the category exists and has any products at all
            from product_recommendations.models import Product

            category_products_exist = Product.objects.filter(
                is_active=True,
                category__name__icontains=category
            ).exists()

            if category_products_exist:
                explanation += (
                    f" While I don’t have that specific item, you can browse other "
                    f"products available under **{category}**."
                )
            else:
                explanation += (
                    f" At the moment, there are no products listed under **{category}**."
                )

        explanation += " You can browse **All Products** or try a more specific search."

        return explanation

    # Case 2: Products found → summarise results
    product_lines = [
        f"- {p.name} (${p.price}) in {p.category.name}"
        for p in products[:5]
    ]

    prompt = f"""
You are a helpful shopping assistant for SmartShop.

User query:
{message}

Detected intent:
Category: {parsed.get("mapped_category") or parsed.get("category")}
Keywords: {parsed.get("keywords")}

Matching products:
{chr(10).join(product_lines)}

Respond concisely and helpfully.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful shopping assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content


import os
import json
from product_recommendations.models import Product

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def generate_product_description(product: Product) -> str:
    """
    Generate a single engaging product description paragraph using OpenAI.
    Uses product attributes + (optional) existing review summary text if available.
    Returns plain text.
    """
    client = _get_openai_client()
    if client is None:
        # fallback: deterministic text (no AI)
        base = product.base_description or ""
        return base.strip() if base else f"{product.name} is available in the {product.category.name} category."

    # Optional: include review summary if you store it somewhere accessible
    # If your review summary is in another model/service, you can integrate later.
    review_summary_text = ""

    prompt = f"""
You are writing a product description for an e-commerce site.

Write ONE short, engaging paragraph (60–90 words) in a friendly, clear tone.
Do not use bullet points. Do not exaggerate. Do not mention that this was AI-generated.

Product details:
- Name: {product.name}
- Category: {product.category.name if product.category else ""}
- Brand: {product.brand or ""}
- Price: {product.price}
- Use case: {product.use_case or ""}
- Base description: {product.base_description or ""}

Customer feedback summary (if any):
{review_summary_text}

Return JSON only in this format:
{{"description": "<text>"}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON safely
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        return (product.base_description or "").strip() or f"{product.name} is available in the {product.category.name} category."

    try:
        data = json.loads(content[start:end+1])
        desc = (data.get("description") or "").strip()
        if desc:
            return desc
    except Exception:
        pass

    return (product.base_description or "").strip() or f"{product.name} is available in the {product.category.name} category."


def get_or_generate_product_description(product: Product, save: bool = True) -> str:
    """
    Returns existing AI description if present; otherwise generates and optionally saves it.
    """
    if product.ai_description and product.ai_description.strip():
        return product.ai_description.strip()

    desc = generate_product_description(product)
    if save:
        product.ai_description = desc
        product.save(update_fields=["ai_description"])
    return desc
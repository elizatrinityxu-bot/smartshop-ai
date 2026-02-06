from django.utils import timezone
from product_recommendations.models import Review
from openai import OpenAI
import os

def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def get_or_generate_review_summary(product):
    """
    Generates or retrieves cached AI summary for product reviews.
    Falls back to a simple heuristic summary when OPENAI_API_KEY is not set.
    """

    reviews = Review.objects.filter(product=product)

    if not reviews.exists():
        return None

    # Check cache (use first review as storage anchor)
    cached_review = reviews.filter(ai_summary_cache__isnull=False).first()

    if cached_review and cached_review.last_summarized_at:
        content = cached_review.ai_summary_cache or ""
        return {
            "summary": extract_summary_only(content) if content else None,
            "sentiment": cached_review.sentiment_label,
            "pros": extract_bullets(content, "Pros"),
            "cons": extract_bullets(content, "Cons"),
        }

    # Build review text bundle
    review_texts = "\n".join(
        [f"- {r.review_text}" for r in reviews]
    )

    # Try to get an OpenAI client; if not present, return a simple fallback summary
    client = _get_openai_client()
    if client is None:
        # Fallback: create a concise summary without calling the API
        excerpt = " ".join([r.review_text for r in reviews][:3])
        summary_text = excerpt[:300] + ("..." if len(excerpt) > 300 else "")
        sentiment = extract_sentiment(summary_text, reviews)

        # Cache fallback summary into the first review so future calls are faster
        first_review = reviews.first()
        first_review.ai_summary_cache = summary_text
        first_review.sentiment_label = sentiment
        first_review.last_summarized_at = timezone.now()
        first_review.save()

        return {
            "summary": summary_text,
            "pros": [],
            "cons": [],
            "sentiment": sentiment,
        }

    # Prepare prompt for the model
    prompt = f"""
    You are an AI assistant summarizing customer reviews for an e-commerce product.

    Customer reviews:
    {review_texts}

    Your task:
    1. Write a concise 2–3 sentence summary.
    2. List clear Pros as bullet points.
    3. List clear Cons as bullet points.
    4. Classify overall sentiment strictly as one of:
    Positive, Neutral, or Negative.

    IMPORTANT:
    - Pros and Cons MUST be bullet points starting with "-"
    - Sentiment MUST be on its own line

    Return EXACTLY in this format:

    Summary:
    <summary text>

    Pros:
    - pro item 1
    - pro item 2

    Cons:
    - con item 1
    - con item 2

    Sentiment:
    <Positive | Neutral | Negative>
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    content = response.choices[0].message.content.strip()

    summary_text = extract_summary_only(content)
    pros = extract_bullets(content, "Pros")
    cons = extract_bullets(content, "Cons")
    sentiment = extract_sentiment(content, reviews) or "Unknown"

    # Cache full model output so we can re-extract Pros/Cons later
    for r in reviews:
        r.ai_summary_cache = content
        r.sentiment_label = sentiment
        r.last_summarized_at = timezone.now()
        r.save()

    return {
        "summary": summary_text,
        "pros": pros,
        "cons": cons,
        "sentiment": sentiment,
    }


from django.db.models import Avg

def extract_sentiment(text, reviews=None):
    # 1) If model provided a direct Sentiment: line, use it
    for line in text.splitlines():
        if line.strip().lower().startswith("sentiment:"):
            val = line.split(":", 1)[1].strip()
            if val:
                return val.capitalize()
            # Empty Sentiment: line -> ignore and fall back to other heuristics

    # 2) If we have reviews, use average rating as a strong signal (primary)
    if reviews is not None:
        avg = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if avg is not None:
            if avg >= 4.0:
                return "Positive"
            if avg <= 2.5:
                return "Negative"
            return "Neutral"

    # 3) Fallback: keyword counting heuristic
    lowered = text.lower()

    positive_words = ["great", "recommend", "effective", "excellent", "love", "good", "satisfied", "amazing", "best", "ideal"]
    negative_words = ["not impressed", "underwhelming", "dislike", "poor", "terrible", "bad", "disappointed", "worse", "didn't", "dont", "did not", "snap"]

    pos = sum(lowered.count(w) for w in positive_words)
    neg = sum(lowered.count(w) for w in negative_words)

    if pos > neg and pos > 0:
        return "Positive"
    if neg > pos and neg > 0:
        return "Negative"

    # Neutral cues
    if "average" in lowered or "okay" in lowered or "decent" in lowered or "mixed" in lowered:
        return "Neutral"

    # If we can't decide, return Unknown so UI shows grey badge
    return "Unknown"


def extract_bullets(text, section):
    lines = text.splitlines()
    bullets = []
    capture = False

    for line in lines:
        if section in line:
            capture = True
            continue
        if capture:
            if line.strip().startswith("-"):
                bullets.append(line.strip("- ").strip())
            elif line.strip() == "":
                continue
            else:
                break

    return bullets

def extract_summary_only(text):
    lines = text.splitlines()
    summary_lines = []

    capture = False
    for line in lines:
        if line.strip().startswith("Summary:"):
            capture = True
            summary_lines.append(line.replace("Summary:", "").strip())
            continue

        if capture:
            if line.strip().startswith(("Pros:", "Cons:", "Sentiment:")):
                break
            if line.strip():
                summary_lines.append(line.strip())

    return " ".join(summary_lines)

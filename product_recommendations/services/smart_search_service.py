import os
import re
from django.db.models import Q
from product_recommendations.models import Product

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

GENERIC_KEYWORDS = {
    "product", "products",
    "item", "items",
    "thing", "things",
    "stuff"
}


def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def _parse_query_with_ai(query):
    """Use OpenAI to parse a natural language query into structured params.
    Returns dict {category: str|None, max_price: float|None, keywords: [str]}
    If the API is not available or parsing fails, returns None to let fallback run.
    """
    client = _get_openai_client()
    if client is None:
        return None

    prompt = f"""
You are a helper that extracts structured search parameters from a user's natural language query for an e-commerce site.
Given a user query, return a JSON object EXACTLY in this format (no extra text):

{{
  "category": "<category name or empty string>",
  "max_price": <number or null>,
  "keywords": ["kw1", "kw2"]
}}

User query: "{query}"

Notes:
- If the user specifies a maximum price (e.g., 'under $1500', 'less than 1000'), set max_price to that number.
- Extract a single most-likely category if present, otherwise empty string.
- Put other meaningful search words into keywords array (no punctuation).
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
    except Exception:
        return None

    content = ""
    if response.choices and getattr(response.choices[0].message, "content", None):
        content = response.choices[0].message.content.strip()

    # Try to extract JSON block from the response
    m = re.search(r"\{[\s\S]*\}", content)
    if not m:
        return None

    try:
        import json
        parsed = json.loads(m.group(0))
        return {
            "category": parsed.get("category") or None,
            "max_price": float(parsed.get("max_price")) if parsed.get("max_price") not in (None, "") else None,
            "keywords": parsed.get("keywords") or []
        }
    except Exception:
        return None


def _parse_query_fallback(query):
    """Fallback heuristic parser: extract 'under $X' price and basic keywords/categories.

    Improvements:
    - Detect multi-word known product phrases (e.g., 'power bank', 'hair dryer') by checking
      n-grams against a small curated list to avoid matching spurious single-token results
      like 'power' matching 'PowerLoop Resistance Bands'.
    - Preserve word order when forming phrases and remove constituent single tokens to
      prefer phrase matches.
    """
    q = query.lower()
    max_price = None
    m = re.search(r"(?:under|less than|below)\s*\$?\s*(\d+[\d,\.]*)", q)
    if m:
        try:
            max_price = float(m.group(1).replace(',', ''))
        except Exception:
            max_price = None

    # keywords: remove stopwords and price tokens
    stop = set(["i", "need", "a", "an", "for", "with", "and", "or", "the", "to", "under", "less", "than", "below", "price", "budget", "get", "recommend", "looking"])
    tokens = re.findall(r"[a-z0-9]+", q)
    tokens = [t for t in tokens if t not in stop and not re.match(r"\d+", t)]

    # Known multi-word phrases to detect in queries (lowercase)
    KNOWN_PHRASES = {"power bank", "hair dryer", "air fryer", "webcam", "vacuum", "sunscreen", "vitamin c", "water bottle", "resistance band", "protein shaker"}

    keywords = []
    i = 0
    while i < len(tokens):
        # try 3-gram then 2-gram then single token
        matched = False
        for n in (3, 2):
            if i + n <= len(tokens):
                phrase = " ".join(tokens[i:i+n])
                if phrase in KNOWN_PHRASES:
                    keywords.append(phrase)
                    i += n
                    matched = True
                    break
        if matched:
            continue
        # otherwise keep single token
        keywords.append(tokens[i])
        i += 1

    return {"category": None, "max_price": max_price, "keywords": keywords}


def _score_and_sort_products(products, keywords, max_price=None):
    """Score products by keyword density (weighted by field) and slight price closeness.

    - Name matches are weighted highest, then brand, then description/use_case/category.
    - If max_price is provided, penalize products that exceed it slightly and give a
      small bonus to products comfortably below it.
    Returns a list of product instances sorted by descending score.
    """
    def _score(p):
        s = 0.0
        name = (p.name or "").lower()
        desc = (p.base_description or "").lower()
        brand = (p.brand or "").lower()
        use_case = (p.use_case or "").lower()
        category = (getattr(p.category, 'name', '') or "").lower()

        for kw in keywords or []:
            kw = kw.lower()
            s += name.count(kw) * 3.0
            s += brand.count(kw) * 2.0
            s += desc.count(kw) * 1.0
            s += use_case.count(kw) * 1.0
            s += category.count(kw) * 1.0

        # small price-based adjustment: prefer items <= max_price, but don't dominate keyword score
        if max_price:
            try:
                price = float(p.price)
                if price > max_price:
                    s -= (price - max_price) / (max_price + 1.0)  # small penalty
                else:
                    s += (max_price - price) / (max_price + 1.0) * 0.5  # small bonus
            except Exception:
                pass
        return s

    prods = list(products)
    scored = [(_score(p), p) for p in prods]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for score, p in scored]


def smart_search_products(query, user=None, return_metadata=False):
    """
    Smart search using AI extraction + database filters.
    When return_metadata is True -> returns (qs_or_list, meta_dict) where meta_dict contains
    parsed params and applied_filters to enable UI transparency.
    """
    if not query:
        return (Product.objects.filter(is_active=True), {"parsed": None, "applied_filters": {}}) if return_metadata else Product.objects.filter(is_active=True)

    query = query.strip()

    params = _parse_query_with_ai(query)
    used_ai = True
    if params is None:
        params = _parse_query_fallback(query)
        used_ai = False

    parsed_category = params.get("category") if params else None
    max_price = params.get("max_price") if params else None
    keywords = params.get("keywords") if params else []

    # Try to map the parsed category to an existing Category name in the DB
    mapped_category = None
    original_category = parsed_category
    if parsed_category:
        try:
            from product_recommendations.models import Category
            # try exact/contains match first
            cat_qs = Category.objects.filter(name__icontains=parsed_category)
            if cat_qs.exists():
                mapped_category = cat_qs.first().name
            else:
                # fuzzy match against available category names
                import difflib
                all_cats = [c.name for c in Category.objects.all()]
                matches = difflib.get_close_matches(parsed_category, all_cats, n=1, cutoff=0.6)
                if matches:
                    mapped_category = matches[0]
                else:
                    mapped_category = None
        except Exception:
            mapped_category = None

    # If the AI parsed a category but we couldn't map it to an existing site category,
    # treat that parsed category as search keyword(s) so the query still filters
    # rather than returning the entire product set.
    if parsed_category and not mapped_category:
        # preserve multi-word phrases like 'hair dryer', 'kitchen appliances' as primary keywords
        # BUT do NOT expand multi-word categories into individual tokens (e.g., don't split 'kitchen appliances' into ['kitchen', 'appliances'])
        # This prevents overly broad matches (e.g., Wi-Fi Plug shouldn't match 'appliances' from 'kitchen appliances')
        parsed_cat_lc = parsed_category.lower()
        if parsed_cat_lc not in (k.lower() for k in (keywords or [])):
            # add the full phrase as a keyword
            if ' ' in parsed_cat_lc:
                keywords = [parsed_cat_lc] + (keywords or [])
            else:
                # single-word categories are added as-is
                keywords = (keywords or []) + [parsed_cat_lc]
        # Only add individual tokens for single-word categories to avoid over-broadening
        if ' ' not in parsed_cat_lc:
            for tk in re.findall(r"[a-z0-9]+", parsed_cat_lc):
                if tk and tk not in keywords:
                    keywords.append(tk)

    base_qs = Product.objects.filter(is_active=True)

    # Debug log
    try:
        print(f"[smart_search] query={query!r} used_ai={used_ai} parsed_category={parsed_category!r} mapped_category={mapped_category!r} max_price={max_price!r} keywords={keywords!r}")
    except Exception:
        pass

    # Remove non-discriminative keywords
    meaningful_keywords = [
        kw for kw in keywords
        if kw.lower() not in GENERIC_KEYWORDS
    ]


    # Build keyword filter Q
    keyword_q = None
    if meaningful_keywords:
        keyword_q = Q()
        for kw in meaningful_keywords:
            keyword_q |= Q(name__icontains=kw)
            keyword_q |= Q(base_description__icontains=kw)
            keyword_q |= Q(brand__icontains=kw)
            keyword_q |= Q(use_case__icontains=kw)
            keyword_q |= Q(category__name__icontains=kw)

    applied = {
        "category_used": False,
        "max_price_used": False,
        "price_relaxed": False,
        "used_ai": used_ai,
    }
    
    applied["keywords_used"] = bool(meaningful_keywords)
    applied["ignored_keywords"] = [
        kw for kw in keywords
        if kw.lower() not in {mk.lower() for mk in meaningful_keywords}
    ]
       

    # 1) Try strict application: category + price + keywords
    qs = base_qs
    if mapped_category:
        qs = qs.filter(category__name__icontains=mapped_category)
        applied["category_used"] = True

    if max_price is not None:
        qs = qs.filter(price__lte=max_price)
        applied["max_price_used"] = True

    if keyword_q is not None:
        qs = qs.filter(keyword_q)

    try:
        print(f"[smart_search] strict-check count={qs.count()}")
    except Exception:
        pass

    if qs.exists():
        if return_metadata:
            return qs.distinct(), {"parsed": {"category": original_category, "mapped_category": mapped_category, "max_price": max_price, "keywords": keywords}, "applied_filters": applied}
        return qs.distinct()

    # 2) If price was applied but no results, try keywords-only with price (ignore category)
    if max_price is not None and keyword_q is not None:
        qs_kw_price = base_qs.filter(price__lte=max_price).filter(keyword_q)
        try:
            print(f"[smart_search] kw+price count={qs_kw_price.count()}")
        except Exception:
            pass
        if qs_kw_price.exists():
            applied["category_used"] = False
            # rank by keyword density & price closeness
            ranked = _score_and_sort_products(qs_kw_price.distinct(), keywords, max_price)
            if return_metadata:
                return ranked, {"parsed": {"category": original_category, "mapped_category": mapped_category, "max_price": max_price, "keywords": keywords}, "applied_filters": applied}
            return ranked

    # 3) If category filtering removed matches but keywords present, try keywords-only (no price)
    if applied["category_used"] and keyword_q is not None:
        qs_kw = base_qs.filter(keyword_q)
        try:
            print(f"[smart_search] kw-only count={qs_kw.count()}")
        except Exception:
            pass
        if qs_kw.exists():
            applied["category_used"] = False
            applied["max_price_used"] = False
            applied["price_relaxed"] = True if max_price is not None else False
            ranked = _score_and_sort_products(qs_kw.distinct(), keywords, max_price)
            if return_metadata:
                return ranked, {"parsed": {"category": original_category, "mapped_category": mapped_category, "max_price": max_price, "keywords": keywords}, "applied_filters": applied}
            return ranked

    # 4) If price was specified but nothing matched, relax price and return best keyword/category matches
    if max_price is not None:
        qs_relaxed = base_qs
        if keyword_q is not None:
            qs_relaxed = qs_relaxed.filter(keyword_q)
        elif mapped_category:
            qs_relaxed = qs_relaxed.filter(category__name__icontains=mapped_category)
        try:
            print(f"[smart_search] relaxed count={qs_relaxed.count()}")
        except Exception:
            pass
        if qs_relaxed.exists():
            applied["price_relaxed"] = True
            applied["max_price_used"] = False
            ranked = _score_and_sort_products(qs_relaxed.distinct(), keywords, max_price)
            if return_metadata:
                return ranked, {"parsed": {"category": original_category, "mapped_category": mapped_category, "max_price": max_price, "keywords": keywords}, "applied_filters": applied}
            return ranked

    # 5) Final fallback: contains on full query
    final_qs = base_qs.filter(
        Q(name__icontains=query) |
        Q(base_description__icontains=query) |
        Q(brand__icontains=query) |
        Q(material__icontains=query) |
        Q(use_case__icontains=query) |
        Q(category__name__icontains=query)
    ).distinct()

    if return_metadata:
        # adjust applied fields
        applied["category_used"] = applied["category_used"] or False
        applied["max_price_used"] = applied["max_price_used"] or False
        # If keywords present, prefer ranking here as well
        if keywords:
            ranked = _score_and_sort_products(final_qs, keywords, max_price)
            return ranked, {"parsed": {"category": original_category, "mapped_category": mapped_category, "max_price": max_price, "keywords": keywords}, "applied_filters": applied}
        return final_qs, {"parsed": {"category": original_category, "mapped_category": mapped_category, "max_price": max_price, "keywords": keywords}, "applied_filters": applied}

    # If keywords known, return a ranked list, otherwise give the raw final_qs
    if keywords:
        return _score_and_sort_products(final_qs, keywords, max_price)

    return final_qs

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from product_recommendations.models import (
    UserProfile,
    Category,
    Product,
    Review
)
import random


class Command(BaseCommand):
    help = "Seed initial data for SmartShop AI-driven e-commerce platform"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🌱 Seeding SmartShop data started..."))

        # =========================================================
        # 1. Create Categories (Prompt 2 – Data Seeding)
        # =========================================================
        category_names = [
            "Electronics & Accessories",
            "Home & Living",
            "Beauty & Personal Care",
            "Fashion & Wearables",
            "Fitness & Wellness",
        ]

        categories = {}
        for name in category_names:
            category, _ = Category.objects.get_or_create(name=name)
            categories[name] = category

        # =========================================================
        # 2. Create Products (20 products, AI-ready)
        # =========================================================
        products_data = [
            # Electronics & Accessories
            {
                "name": "PulseSound Wireless Earbuds",
                "category": "Electronics & Accessories",
                "price": 129.00,
                "base_description": "PulseSound Wireless Earbuds are designed for everyday use, delivering clear audio, stable Bluetooth connectivity, and a comfortable in-ear fit suitable for workouts and commuting.",
                "brand": "PulseSound",
                "material": "ABS plastic, silicone ear tips",
                "use_case": "Gym, commuting, calls",
                "care_instructions": "Wipe with dry cloth, avoid water exposure",
                "image_url": "/media/products/pulsesound_earbuds.png",
            },
            {
                "name": "VoltMax 20000mAh Power Bank",
                "category": "Electronics & Accessories",
                "price": 89.00,
                "base_description": "VoltMax Power Bank offers high-capacity portable charging, making it ideal for travel, long workdays, and heavy smartphone users.",
                "brand": "VoltMax",
                "material": "Aluminum alloy",
                "use_case": "Travel, daily charging",
                "care_instructions": "Keep dry, avoid extreme heat",
                "image_url": "/media/products/voltmax_powerbank.png",
            },
            {
                "name": "SmartHome Wi-Fi Plug",
                "category": "Electronics & Accessories",
                "price": 39.00,
                "base_description": "SmartHome Wi-Fi Plug enables remote control of household appliances, allowing users to automate and monitor energy usage conveniently.",
                "brand": "SmartHome",
                "material": "Fire-retardant plastic",
                "use_case": "Home automation",
                "care_instructions": "Indoor use only",
                "image_url": "/media/products/smarthome_wifi_plug.png",
            },
            {
                "name": "ClearView HD Webcam",
                "category": "Electronics & Accessories",
                "price": 99.00,
                "base_description": "ClearView HD Webcam delivers sharp video quality and reliable performance for online meetings, remote work, and video calls.",
                "brand": "ClearView",
                "material": "Plastic body, glass lens",
                "use_case": "Remote work, video calls",
                "care_instructions": "Clean lens with microfiber cloth",
                "image_url": "/media/products/clearview_webcam.png",
            },

            # Home & Living
            {
                "name": "AirCrisp Digital Air Fryer",
                "category": "Home & Living",
                "price": 199.00,
                "base_description": "AirCrisp Digital Air Fryer allows users to prepare healthier meals at home with minimal oil while maintaining consistent cooking results.",
                "brand": "AirCrisp",
                "material": "Stainless steel, heat-resistant plastic",
                "use_case": "Home cooking",
                "care_instructions": "Hand wash basket, wipe exterior",
                "image_url": "/media/products/aircrisp_airfryer.png",
            },
            {
                "name": "PureMist Aroma Diffuser",
                "category": "Home & Living",
                "price": 69.00,
                "base_description": "PureMist Aroma Diffuser enhances indoor ambience by dispersing fine mist infused with essential oils for relaxation and comfort.",
                "brand": "PureMist",
                "material": "PP plastic",
                "use_case": "Relaxation, sleep",
                "care_instructions": "Empty water tank after use",
                "image_url": "/media/products/puremist_diffuser.png",
            },
            {
                "name": "BrightLite Adjustable Desk Lamp",
                "category": "Home & Living",
                "price": 59.00,
                "base_description": "BrightLite Desk Lamp provides adjustable lighting suitable for studying, working, and reading in home or office environments.",
                "brand": "BrightLite",
                "material": "Aluminum, ABS",
                "use_case": "Study, office desk",
                "care_instructions": "Unplug before cleaning",
                "image_url": "/media/products/brightlite_lamp.png",
            },
            {
                "name": "RoboClean Compact Vacuum",
                "category": "Home & Living",
                "price": 249.00,
                "base_description": "RoboClean Compact Vacuum offers powerful suction in a compact form, ideal for small apartments and daily cleaning needs.",
                "brand": "RoboClean",
                "material": "Plastic, rubber wheels",
                "use_case": "Home cleaning",
                "care_instructions": "Clean filter weekly",
                "image_url": "/media/products/roboclean_vacuum.png",
            },

            # Beauty & Personal Care
            {
                "name": "GlowPure Facial Cleanser",
                "category": "Beauty & Personal Care",
                "price": 29.00,
                "base_description": "GlowPure Facial Cleanser gently removes impurities while maintaining skin hydration, suitable for daily skincare routines.",
                "brand": "GlowPure",
                "ingredients": "Aloe vera, glycerin",
                "use_case": "Daily facial cleansing",
                "care_instructions": "Store in cool, dry place",
                "image_url": "/media/products/glowpure_cleanser.png",
            },
            {
                "name": "SunGuard SPF50 Sunscreen",
                "category": "Beauty & Personal Care",
                "price": 39.00,
                "base_description": "SunGuard SPF50 Sunscreen provides broad-spectrum protection against UV rays, suitable for outdoor activities and daily use.",
                "brand": "SunGuard",
                "ingredients": "Zinc oxide, vitamin E",
                "use_case": "Outdoor protection",
                "care_instructions": "Avoid direct sunlight storage",
                "image_url": "/media/products/sunguard_sunscreen.png",
            },
            {
                "name": "SilkSmooth Ionic Hair Dryer",
                "category": "Beauty & Personal Care",
                "price": 149.00,
                "base_description": "SilkSmooth Ionic Hair Dryer delivers fast drying performance with reduced heat damage, making it suitable for daily hair styling at home.",
                "brand": "SilkSmooth",
                "material": "ABS plastic, ceramic heating element",
                "use_case": "Hair styling",
                "care_instructions": "Unplug after use",
                "image_url": "/media/products/silksmooth_dryer.png",
            },
            {
                "name": "VitaGlow Vitamin C Serum",
                "category": "Beauty & Personal Care",
                "price": 59.00,
                "base_description": "VitaGlow Vitamin C Serum helps brighten skin tone and improve texture, suitable for users seeking a simple skincare routine.",
                "brand": "VitaGlow",
                "ingredients": "Vitamin C, hyaluronic acid",
                "use_case": "Skincare",
                "care_instructions": "Store in cool place",
                "image_url": "/media/products/vitaglow_serum.png",
            },

            # Fashion & Wearables
            {
                "name": "FlexRun Lightweight Running Shoes",
                "category": "Fashion & Wearables",
                "price": 159.00,
                "base_description": "FlexRun Running Shoes are designed for comfort and support, suitable for jogging, training, and everyday active wear.",
                "brand": "FlexRun",
                "material": "Mesh fabric, rubber sole",
                "use_case": "Running, training",
                "care_instructions": "Hand wash, air dry",
                "image_url": "/media/products/flexrun_shoes.png",
            },
            {
                "name": "UrbanCarry Canvas Tote Bag",
                "category": "Fashion & Wearables",
                "price": 49.00,
                "base_description": "UrbanCarry Tote Bag offers practical storage with a minimalist design, suitable for daily errands and casual use.",
                "brand": "UrbanCarry",
                "material": "Canvas cotton",
                "use_case": "Daily carry",
                "care_instructions": "Spot clean only",
                "image_url": "/media/products/urbancarry_tote.png",
            },
            {
                "name": "ClassicFit Casual Hoodie",
                "category": "Fashion & Wearables",
                "price": 79.00,
                "base_description": "ClassicFit Casual Hoodie offers comfort and warmth with a relaxed fit for everyday casual wear.",
                "brand": "ClassicFit",
                "material": "Cotton blend",
                "use_case": "Casual wear",
                "care_instructions": "Machine wash cold",
                "image_url": "/media/products/classicfit_hoodie.png",
            },
            {
                "name": "TimePro Minimalist Watch",
                "category": "Fashion & Wearables",
                "price": 199.00,
                "base_description": "TimePro Minimalist Watch combines clean design with reliable timekeeping, suitable for office and lifestyle wear.",
                "brand": "TimePro",
                "material": "Stainless steel, leather strap",
                "use_case": "Office, lifestyle",
                "care_instructions": "Avoid water immersion",
                "image_url": "/media/products/timepro_watch.png",
            },

            # Fitness & Wellness
            {
                "name": "FlexFlow Yoga Mat",
                "category": "Fitness & Wellness",
                "price": 59.00,
                "base_description": "FlexFlow Yoga Mat provides cushioned support and stability, making it ideal for yoga and stretching routines.",
                "brand": "FlexFlow",
                "material": "TPE foam",
                "use_case": "Yoga, stretching",
                "care_instructions": "Wipe after use",
                "image_url": "/media/products/flexflow_mat.png",
            },
            {
                "name": "PowerLoop Resistance Bands",
                "category": "Fitness & Wellness",
                "price": 49.00,
                "base_description": "PowerLoop Resistance Bands support strength training and flexibility exercises across fitness levels.",
                "brand": "PowerLoop",
                "material": "Natural latex",
                "use_case": "Strength training",
                "care_instructions": "Store away from sunlight",
                "image_url": "/media/products/powerloop_bands.png",
            },
            {
                "name": "IronCore Adjustable Dumbbells",
                "category": "Fitness & Wellness",
                "price": 299.00,
                "base_description": "IronCore Adjustable Dumbbells provide flexible weight training options for home workouts.",
                "brand": "IronCore",
                "material": "Cast iron, rubber coating",
                "use_case": "Strength training",
                "care_instructions": "Wipe after use",
                "image_url": "/media/products/ironcore_dumbbells.png",
            },
            {
                "name": "ShakeSmart Protein Shaker",
                "category": "Fitness & Wellness",
                "price": 29.00,
                "base_description": "ShakeSmart Protein Shaker offers a convenient solution for mixing supplements and nutrition drinks.",
                "brand": "ShakeSmart",
                "material": "BPA-free plastic",
                "use_case": "Nutrition, gym",
                "care_instructions": "Dishwasher safe",
                "image_url": "/media/products/shakesmart_shaker.png",
            },
        ]

        product_objects = []
        for data in products_data:
            product, _ = Product.objects.update_or_create(
                name=data["name"],
                defaults={
                    "category": categories[data["category"]],
                    "price": data["price"],
                    "base_description": data["base_description"],
                    "brand": data.get("brand"),
                    "material": data.get("material"),
                    "ingredients": data.get("ingredients"),
                    "use_case": data.get("use_case"),
                    "care_instructions": data.get("care_instructions"),
                    "image_url": data.get("image_url"),
                    "stock": 50,
                    "is_active": True,
                },
            )
            product_objects.append(product)

        # =========================================================
        # 3. Create Users + Profiles (10 users)
        # =========================================================
        user_profiles = [
            ("Alex Tan", "Electronics & Accessories,Fitness & Wellness", "high", "performance", "gym"),
            ("Bella Xu", "Beauty & Personal Care,Fashion & Wearables", "medium", "stylish", "daily"),
            ("Chris Yeo", "Home & Living,Electronics & Accessories", "medium", "practical", "home"),
            ("Diana Lim", "Fashion & Wearables", "low", "friendly", "casual"),
            ("Ethan Wong", "Fitness & Wellness", "high", "performance", "training"),
            ("Fiona Lee", "Beauty & Personal Care", "medium", "gentle", "skincare"),
            ("George Tan", "Electronics & Accessories", "high", "technical", "work"),
            ("Hannah Goh", "Home & Living", "medium", "practical", "home"),
            ("Ivan Koh", "Fitness & Wellness,Fashion & Wearables", "low", "energetic", "outdoor"),
            ("Julia Ng", "Beauty & Personal Care,Home & Living", "medium", "calm", "relaxation"),
        ]

        for username, prefs, budget, tone, context in user_profiles:
            user, created = User.objects.get_or_create(
                username=username,
                email = username.lower().replace(" ", ".") + "@example.com"
            )
            if created:
                user.set_password("password123")
                user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "preferred_categories": prefs,
                    "budget_level": budget,
                    "tone_preference": tone,
                    "usage_context": context,
                },
            )

        users = User.objects.filter(username__in=[u[0] for u in user_profiles])

        # =========================================================
        # 4. Create Reviews (8 per product, mixed sentiment)
        #    Use templates that include product context so each product
        #    gets unique review text (helps AI produce distinct summaries)
        # =========================================================
        # Category-specific review templates to produce more diverse reviews
        category_templates = {
            "Electronics & Accessories": [
                ("Clear audio and excellent connectivity for {product}.", 5),
                ("Battery life is decent, but could be longer for heavy users.", 4),
                ("Good build quality but occasional connectivity hiccups.", 3),
                ("Not impressed with the battery life on {product}.", 2),
                ("Comfortable fit and great for workouts.", 5),
                ("Would recommend {product} to those needing reliable audio.", 5),
                ("A solid option for the price.", 4),
                ("Average performance in noisy environments.", 3),
            ],
            "Home & Living": [
                ("Bright adjustable light and good build for {product}.", 5),
                ("Stylish design and easy to assemble.", 4),
                ("Works well but a bit heavier than expected.", 3),
                ("Stopped working after a few weeks for me.", 2),
                ("Great value and very functional.", 5),
                ("Would recommend for home use.", 5),
                ("The finish could be better.", 3),
                ("Base is a bit wobbly on my desk.", 2),
            ],
            "Beauty & Personal Care": [
                # General skincare templates (used when product is a cleanser/serum/sunscreen)
                ("Gentle and non-greasy, works well for sensitive skin.", 5),
                ("Noticeable improvement after regular use.", 4),
                ("Good texture but results varied for me.", 3),
                ("Caused some breakouts for my skin type.", 2),
                ("Lightweight and absorbs quickly.", 5),
                ("Would recommend to friends.", 5),
                ("Packaging could be improved.", 3),
                ("Didn't see the promised results.", 2),
            ],
            # Hair dryer specific templates (for products with 'hair' or 'dryer' in the name)
            "Hair Dryer": [
                ("Powerful airflow and dries hair quickly without excessive heat.", 5),
                ("Lightweight and ergonomic, easy to handle during styling.", 4),
                ("Motor is a bit noisy but performance is decent.", 3),
                ("Heats too much on high setting and dries out hair.", 2),
                ("Great value for the performance and styling features.", 5),
                ("Would recommend this hair dryer for home use.", 5),
                ("Attachments are useful but could be better designed.", 3),
                ("Cord length is short for my setup.", 2),
            ],
            "Fashion & Wearables": [
                ("Comfortable fit and true to size for {product}.", 5),
                ("High-quality fabric and good stitching.", 4),
                ("Color faded slightly after washing.", 3),
                ("Material felt cheap for the price.", 2),
                ("Very flattering fit and comfortable.", 5),
                ("Would buy again.", 5),
                ("Sizing runs a bit small.", 3),
                ("Not very durable over months of use.", 2),
            ],
            "Fitness & Wellness": [
                ("Well-suited for home and gym workouts with solid performance.", 5),
                ("Durable and holds up to regular training.", 4),
                ("Comfortable and functional for most users.", 3),
                ("Some durability concerns under heavy use.", 2),
                ("Ideal for a range of fitness routines.", 5),
                ("Would recommend to fitness enthusiasts.", 5),
                ("Good performance for the price.", 4),
                ("May not be ideal for all specialized exercise needs.", 3),
            ],
        }

        # Product subtype templates for more accurate, product-specific reviews
        subtype_templates = {
            "earbud": [
                ("Clear audio with balanced bass for {product} — great for music and calls.", 5),
                ("Comfortable fit for long listening sessions.", 4),
                ("Connectivity occasionally drops in crowded areas.", 3),
                ("Battery drains faster under heavy use.", 2),
                ("Excellent sound quality for the price.", 5),
                ("Would recommend for workouts and commuting.", 5),
                ("Case could be more compact.", 3),
                ("Not very loud in noisy environments.", 3),
            ],
            "webcam": [
                ("Sharp video quality and accurate color reproduction for {product}.", 5),
                ("Good low-light performance and reliable autofocus.", 4),
                ("Microphone could be clearer in some environments.", 3),
                ("Drivers were a bit finicky to set up.", 2),
                ("Great for video calls and streaming.", 5),
                ("Would recommend for remote work.", 5),
            ],
            "power bank": [
                ("High capacity and reliable charging for {product}.", 5),
                ("Charges multiple devices quickly.", 4),
                ("Bulkier than expected for a portable unit.", 3),
                ("Took a long time to recharge the power bank itself.", 2),
                ("Solid build quality and dependable output.", 5),
            ],
            "plug": [
                ("Easy setup and stable Wi-Fi connection for {product}.", 5),
                ("Works well with smart home apps.", 4),
                ("Occasional disconnects when network is busy.", 3),
                ("App integration could be more intuitive.", 2),
                ("Great value for the convenience.", 5),
            ],
            "air fryer": [
                ("Cooks evenly and produces crisp results with minimal oil.", 5),
                ("Simple controls and easy to clean.", 4),
                ("Takes longer for larger batches.", 3),
                ("A bit noisy on high heat settings.", 2),
            ],
            "diffuser": [
                ("Quiet operation and fine mist output for great diffusion.", 5),
                ("Looks stylish and blends with decor.", 4),
                ("Tank capacity is smaller than expected.", 3),
            ],
            "cleanser": [
                ("Gentle cleanser that removes impurities without drying out skin.", 5),
                ("Pleasant texture and easy to rinse.", 4),
                ("Did not see noticeable results for my skin type.", 3),
                ("Caused irritation for sensitive skin users.", 2),
            ],
            "sunscreen": [
                ("Lightweight, non-greasy sunscreen with good protection.", 5),
                ("Absorbs quickly and doesn't leave a white cast.", 4),
                ("Needs reapplication for long sun exposure.", 3),
            ],
            "hair dryer": [
                ("Powerful airflow and dries hair quickly without excessive heat.", 5),
                ("Lightweight and ergonomic, easy to handle during styling.", 4),
                ("Motor is a bit noisy but performance is decent.", 3),
                ("Heats too much on high setting and dries out hair.", 2),
                ("Great value for the performance and styling features.", 5),
            ],
            "vacuum": [
                ("Strong suction and efficient cleaning for various floor types.", 5),
                ("Compact design and easy to maneuver around furniture.", 4),
                ("Dustbin capacity could be larger for heavy use.", 3),
                ("Brushes can get clogged with long hair.", 2),
            ],
            "lamp": [
                ("Adjustable brightness and sturdy build make {product} great for desks.", 5),
                ("Stylish look and compact footprint.", 4),
                ("Light could be brighter for large workspaces.", 3),
                ("Base wobbles slightly on uneven surfaces.", 2),
            ],
            "shaker": [
                ("Mixes powders thoroughly and seals well, ideal for post-workout shakes.", 5),
                ("Leak-proof lid and easy to clean.", 4),
                ("Some residue can stick to the corners, needs a thorough wash.", 3),
                ("Plastic smells faint after first few uses for some users.", 2),
            ],
            "dumbbell": [
                ("Adjustable weights are convenient and solidly built.", 5),
                ("Compact storage and smooth adjustment mechanism.", 4),
                ("Plating scratched after heavy use.", 3),
                ("Locking mechanism can be finicky.", 2),
            ],
            "resistance": [
                ("Durable bands with consistent tension and good grip.", 5),
                ("Portable and ideal for a variety of exercises.", 4),
                ("Bands can snap under extreme strain.", 2),
            ],
            "yoga": [
                ("Provides cushioned support and good traction for yoga routines.", 5),
                ("Non-slip surface and easy to roll up.", 4),
                ("Material picks up sweat and needs regular cleaning.", 3),
            ],
            "shoe": [
                ("Comfortable fit and excellent cushioning for long runs.", 5),
                ("Durable outsole and breathable upper.", 4),
                ("Sizing can be off for some users.", 3),
            ],
            "tote": [
                ("Spacious interior and sturdy construction, great for everyday use.", 5),
                ("Comfortable straps and well-made canvas material.", 4),
                ("Could use inner pockets for organization.", 3),
                ("Color faded after several washes for some users.", 2),
            ],
            "watch": [
                ("Minimalist design with accurate timekeeping and good battery life.", 5),
                ("Lightweight and comfortable for daily wear.", 4),
                ("Band may feel stiff initially.", 3),
                ("Not water resistant enough for heavy activity.", 2),
            ],
            "default": [
                ("Good quality and meets expectations for {product}.", 5),
                ("Reasonably priced and functional.", 4),
                ("Average performance in some situations.", 3),
                ("Not impressed with durability over time.", 2),
            ]
        }

        for product in product_objects:
            # Replace existing reviews for a deterministic seed
            Review.objects.filter(product=product).delete()

            # Look for subtype hints in the name or base_description using multiple keywords
            lower_name = product.name.lower()
            lower_desc = (product.base_description or "").lower()

            # mapping subtype -> list of keywords to match
            subtype_keywords = {
                "earbud": ["earbud", "earbuds", "earphones", "pulsesound"],
                "webcam": ["webcam", "camera", "clearview"],
                "power bank": ["power bank", "powerbank", "voltmax"],
                "plug": ["plug", "smart plug", "wifi plug", "smarthome"],
                "air fryer": ["air fryer", "airfryer", "aircrisp"],
                "diffuser": ["diffuser", "puremist"],
                "cleanser": ["cleanser", "cleanser", "cleanse", "glowpure"],
                "sunscreen": ["sunscreen", "spf", "sunguard"],
                "hair dryer": ["hair dryer", "dryer", "silksmooth"],
                "vacuum": ["vacuum", "roboclean", "vacuum"],
                "lamp": ["lamp", "desk lamp", "brightlite"],
                "shaker": ["shaker", "shake", "protein", "shakesmart"],
                "dumbbell": ["dumbbell", "adjustable dumbbell", "ironcore"],
                "resistance": ["resistance", "band", "powerloop"],
                "yoga": ["yoga", "mat", "flexflow"],
                "shoe": ["shoe", "shoes", "running", "flexrun"],
            }

            selected_templates = None
            for key, keywords in subtype_keywords.items():
                for kw in keywords:
                    if kw in lower_name or kw in lower_desc:
                        # if subtype templates exist for this key, prefer them
                        selected_templates = subtype_templates.get(key) or subtype_templates.get("default")
                        break
                if selected_templates:
                    break

            # Fall back to category templates if no subtype detected
            if selected_templates is None:
                templates = category_templates.get(product.category.name, subtype_templates["default"])
                templates_to_use = templates
            else:
                templates_to_use = selected_templates

            for template, rating in templates_to_use:
                text = template.format(
                    product=product.name,
                    brand=(product.brand or product.name),
                    category=product.category.name
                )
                Review.objects.create(
                    product=product,
                    user=random.choice(users),
                    rating=rating,
                    review_text=text,
                )

        self.stdout.write(self.style.SUCCESS("✅ SmartShop data seeding completed successfully!"))

"""Seed sample reviews and run real Select AI sentiment analysis on them.

Standalone helper for demos when live web scraping is blocked by review sites.
Inserts a handful of realistic reviews for a brand into scraped_reviews, then
runs the actual SentimentAgent (DBMS_CLOUD_AI via the Select AI profile) so the
dashboard has genuine, model-produced sentiment to display.

Usage:  python seed_reviews.py [brand]   # default brand: Nike
"""

import asyncio
import sys

import oracledb

from config import settings
from database import connect_to_database, get_db_connection
from sentiment_agent import SentimentAgent

BRAND = sys.argv[1] if len(sys.argv) > 1 else "Nike"
TOPIC = "customer sentiment"

# Brand-specific sample review sets. Keyed by lowercased brand name; falls back
# to GENERIC_REVIEWS for any brand without a curated set.
NIKE_REVIEWS = [
    ("trustpilot.com", "Verified Buyer",
     "The running shoes are incredibly comfortable and the delivery was fast. "
     "Best purchase I've made this year, my knees no longer hurt after long runs."),
    ("reddit.com", "r/running user",
     "Ordered two pairs and one arrived with a defect. Customer service took "
     "three weeks to respond and I'm still waiting on my refund. Really frustrating."),
    ("consumeraffairs.com", "Long-time customer",
     "Quality has gone downhill over the past few years. The materials feel "
     "cheaper than they used to and the prices keep going up. Disappointed."),
    ("reviews.io", "Marathon runner",
     "Absolutely love the new collection. Great support, stylish design, and the "
     "app tracking integration works flawlessly. Highly recommend to any athlete."),
    ("g2.com", "Retail partner",
     "Decent products overall but the sizing is inconsistent between models. "
     "Some fit true to size, others run small. Wish they'd standardize it."),
    ("yelp.com", "First-time buyer",
     "The store staff were helpful and friendly, but the item I wanted was out "
     "of stock in three sizes. Ended up ordering online and it was fine."),
    ("trustpilot.com", "Frequent shopper",
     "Shipping is reliable and returns are painless. I've bought from them for "
     "years and never had a serious problem. Solid, dependable brand."),
    ("reddit.com", "r/sneakers user",
     "Hyped release sold out in seconds to bots and now resellers want triple "
     "the price. The launch process is broken and it's ruining the community."),
]

APPLE_REVIEWS = [
    ("trustpilot.com", "Verified Buyer",
     "The new iPhone camera is stunning and the battery easily lasts all day. "
     "Setup from my old phone was seamless. Worth every penny in my opinion."),
    ("reddit.com", "r/apple user",
     "Battery health dropped to 82% after barely a year and they wanted $99 to "
     "replace it. Feels like planned obsolescence. Really disappointing from Apple."),
    ("consumeraffairs.com", "Long-time customer",
     "Prices keep climbing every generation while the base storage stays tiny. "
     "You're forced to pay more for a usable model. Getting tired of it."),
    ("reviews.io", "Creative professional",
     "The MacBook Pro with the new chip is incredibly fast and silent. Renders "
     "that took minutes now take seconds. Best laptop I have ever owned."),
    ("g2.com", "IT administrator",
     "Solid hardware but the ecosystem lock-in is frustrating for mixed fleets. "
     "Great for users, harder for admins. Support has been responsive though."),
    ("yelp.com", "Apple Store visitor",
     "Genius Bar staff were friendly but I waited 40 minutes past my appointment. "
     "They fixed the issue for free under warranty, so it ended well."),
    ("trustpilot.com", "Frequent shopper",
     "AirPods and the Watch just work together flawlessly. The integration across "
     "devices is unmatched. I keep coming back despite the premium price."),
    ("reddit.com", "r/ios user",
     "The latest iOS update drained my battery and made older apps crash. "
     "Feels rushed and buggy. Hoping the next patch fixes these problems soon."),
]

GENERIC_REVIEWS = [
    ("trustpilot.com", "Verified Buyer",
     f"Overall a great experience with {BRAND}. The product quality is excellent "
     "and delivery was fast. Would happily recommend to friends and family."),
    ("reddit.com", "community user",
     f"Had a rough time with {BRAND} support. It took weeks to get a response and "
     "my issue is still unresolved. The wait times are genuinely frustrating."),
    ("consumeraffairs.com", "Long-time customer",
     f"I've noticed {BRAND}'s quality slipping while prices keep rising. Not sure "
     "it's worth the premium anymore. A bit disappointed after years of loyalty."),
    ("reviews.io", "Happy customer",
     f"Absolutely love what {BRAND} has been doing lately. Great design, reliable "
     "performance, and the value is fantastic. Highly recommend."),
    ("g2.com", "Business user",
     f"{BRAND} works well for our needs but the onboarding was confusing. Once set "
     "up it's solid. Support has been helpful when we reached out."),
    ("yelp.com", "First-time buyer",
     f"Staff at {BRAND} were friendly and helpful, though the item I wanted was out "
     "of stock. Ended up ordering online and it arrived fine."),
    ("trustpilot.com", "Frequent shopper",
     f"Reliable and consistent. I've used {BRAND} for years without any serious "
     "problems. Dependable and trustworthy."),
    ("reddit.com", "power user",
     f"The recent {BRAND} changes feel rushed and buggy. Some features regressed "
     "and it's annoying. Hoping they address the complaints soon."),
]

REVIEWS_BY_BRAND = {
    "nike": NIKE_REVIEWS,
    "apple": APPLE_REVIEWS,
}
SAMPLE_REVIEWS = REVIEWS_BY_BRAND.get(BRAND.lower(), GENERIC_REVIEWS)


def _insert_reviews() -> list[int]:
    conn = get_db_connection()
    cur = conn.cursor()
    ids: list[int] = []
    for i, (source, author, text) in enumerate(SAMPLE_REVIEWS):
        url = f"https://{source}/review/{BRAND.lower().replace(' ', '')}/sample-{i}"
        cur.execute(
            "SELECT id FROM scraped_reviews WHERE url = :u FETCH FIRST 1 ROW ONLY",
            {"u": url},
        )
        if cur.fetchone():
            continue
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """
            INSERT INTO scraped_reviews
                (source, url, author, review_text, brand, product, region, scraped_at)
            VALUES (:source, :url, :author, :text, :brand, :product, NULL, SYSTIMESTAMP)
            RETURNING id INTO :new_id
            """,
            {"source": source, "url": url, "author": author, "text": text,
             "brand": BRAND, "product": TOPIC, "new_id": new_id},
        )
        returned = new_id.getvalue()
        ids.append(int(returned[0] if isinstance(returned, list) else returned))
    conn.commit()
    conn.close()
    return ids


async def main() -> None:
    await connect_to_database()
    ids = await asyncio.to_thread(_insert_reviews)
    print(f"Inserted {len(ids)} new reviews for '{BRAND}': {ids}")

    agent = SentimentAgent()
    results = await agent.analyze_reviews(brand=BRAND)
    print(f"Analyzed {len(results)} reviews via Select AI profile "
          f"'{settings.SELECT_AI_PROFILE}'.")
    for r in results:
        print(f"  review {r.get('review_id')}: "
              f"{r.get('sentiment')} ({r.get('score')})")


if __name__ == "__main__":
    asyncio.run(main())

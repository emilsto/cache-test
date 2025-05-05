import redis
import uuid
import random
from faker import Faker
import time

# --- Configuration ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0  # Use database 0

NUM_FEEDS = 100       # How many feeds to create
MAX_ITEMS_PER_FEED = 1000 # Maximum items per feed (will be random up to this)
MIN_ITEMS_PER_FEED = 1000 # Minimum items per feed

# Optional: Clear the database before seeding?
FLUSH_DB_BEFORE_SEED = True

# --- Initialize ---
fake = Faker()
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    r.ping() # Check connection
    print(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}, DB {REDIS_DB}")
except redis.exceptions.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
    exit(1)

# --- Seeding Logic ---

def create_feed_and_items(feed_id):
    """Creates items for a given feed_id and populates Redis."""
    start_time = time.time()
    print(f"--- Seeding Feed ID: {feed_id} ---")

    feed_type = random.choice(['product', 'article', 'service', 'event'])
    feed_name = f"{fake.bs().title()} Feed ({feed_type})"
    feed_created_at = fake.iso8601() # Or use time.time()

    # --- Redis Key Definitions ---
    # Index Set key: Stores item IDs belonging to this feed
    feed_index_key = f"feed:{feed_id}:items"
    # Optional: Store feed metadata in a separate Hash
    feed_meta_key = f"feed:{feed_id}:meta"

    # --- Pipeline for Efficiency ---
    # Use a pipeline to batch commands for this feed
    pipe = r.pipeline()

    # 1. Optional: Store Feed Metadata
    pipe.hset(feed_meta_key, mapping={
        "id": feed_id,
        "type": feed_type,
        "name": feed_name,
        "created_at": feed_created_at,
        "status": "active" # Example extra field
    })
    # Set an expiry for the metadata if desired (e.g., 1 day)
    # pipe.expire(feed_meta_key, 86400)

    # 2. Generate and Store Items
    num_items = random.randint(MIN_ITEMS_PER_FEED, MAX_ITEMS_PER_FEED)
    item_keys_for_index = [] # Keep track of keys to add to the index Set

    print(f"Generating {num_items} items for feed {feed_id}...")

    for i in range(num_items):
        item_id = str(uuid.uuid4()) # Generate unique item ID
        item_key = f"item:{item_id}" # Redis key for the item hash

        item_data = {
            # Note: We don't store feed_id IN the item hash itself,
            # as we derive the relationship from the feed_index_key.
            # You could add it if needed for other query patterns.
            "price": f"{random.uniform(1.99, 999.99):.2f}",
            "description": fake.text(max_nb_chars=200),
            "name": fake.bs().title() if feed_type == 'product' else fake.catch_phrase(),
            "cta": random.choice(["Buy Now", "Learn More", "View Details", "Shop", "Read Article", "Register"]),
            "clickUrl": fake.url(),
            "item_id_ref": item_id # Storing the ID itself can sometimes be useful
        }

        # Add HSET command for the item to the pipeline
        pipe.hset(item_key, mapping=item_data)
        # Optionally set an expiry per item
        # pipe.expire(item_key, 86400) # e.g., 1 day

        item_keys_for_index.append(item_key) # Add key to list for index

        if (i + 1) % 200 == 0: # Progress indicator within item generation
             print(f"  ... generated {i + 1}/{num_items} items")


    # 3. Add all Item Keys to the Feed's Index Set
    if item_keys_for_index:
        # The SADD command can take multiple members at once
        pipe.sadd(feed_index_key, *item_keys_for_index)
        # Optionally set an expiry for the index itself
        # pipe.expire(feed_index_key, 86400) # e.g., 1 day
    else:
        print(f"Feed {feed_id} has no items to add to index.")


    # --- Execute the Pipeline ---
    try:
        results = pipe.execute()
        # results is a list containing the result of each command in the pipeline
        # Check for errors if needed, though pipeline errors can be tricky
        # print(f"Pipeline execution results (length): {len(results)}")
        duration = time.time() - start_time
        print(f"Successfully seeded Feed ID: {feed_id} with {num_items} items in {duration:.2f} seconds.")
        # Quick verification
        item_count = r.scard(feed_index_key)
        print(f"Verification: SCARD {feed_index_key} = {item_count}")

    except redis.RedisError as e:
        print(f"Error executing pipeline for feed {feed_id}: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    total_start_time = time.time()
    print("Starting Redis Seed Script...")

    if FLUSH_DB_BEFORE_SEED:
        print(f"Flushing Redis DB: {REDIS_DB}...")
        r.flushdb()
        print("DB Flushed.")

    # Assume feed IDs are integers for simplicity, like from a Postgres sequence
    for i in range(1, NUM_FEEDS + 1):
        create_feed_and_items(i)

    total_duration = time.time() - total_start_time
    print("\n--------------------")
    print(f"Seeding Complete!")
    print(f"Total Feeds Created: {NUM_FEEDS}")
    print(f"Total Time: {total_duration:.2f} seconds")
    print("--------------------")
    print("Example commands to check data:")
    print(f"  KEYS 'feed:*:*'")
    print(f"  KEYS 'item:*'")
    print(f"  HGETALL feed:1:meta")
    print(f"  SCARD feed:1:items")
    print(f"  SMEMBERS feed:1:items")
    print(f"  SRANDMEMBER feed:1:items 5")
    print(f"  HGETALL <some_item_key_from_smembers>")

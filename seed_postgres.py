import psycopg2
import random
import uuid
from faker import Faker

fake = Faker()

DB_CONFIG = {
    'dbname': 'mydatabase',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()

        # Step 1: Drop tables
        print("Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS items;")
        cur.execute("DROP TABLE IF EXISTS feeds;")

        # Step 2: Recreate tables
        print("Creating tables...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'active'
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                feed_id INTEGER NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                description TEXT NOT NULL,
                name VARCHAR(255) NOT NULL,
                cta VARCHAR(50) NOT NULL,
                click_url TEXT NOT NULL,
                item_id_ref UUID NOT NULL DEFAULT gen_random_uuid(),
                FOREIGN KEY (feed_id) REFERENCES feeds(id)
            );
        """)

        # Step 3: Insert 100 feeds
        print("Inserting feeds...")
        feeds_data = []
        for feed_id in range(1, 101):
            feed_type = random.choice(['product', 'article', 'service', 'event'])
            feed_name = fake.bs().title() if feed_type == 'product' else fake.catch_phrase()
            feeds_data.append((feed_id, feed_type, feed_name))
            print(f"Feed {feed_id} inserted.")

        cur.executemany("""
            INSERT INTO feeds (id, type, name)
            VALUES (%s, %s, %s)
        """, feeds_data)

        # Step 4: Insert 1000 items per feed
        print("Inserting items...")
        items_data = []
        for feed_id in range(1, 101):
            print(f"Processing feed {feed_id}...")
            for item_idx in range(1000):
                price = round(random.uniform(1.99, 999.99), 2)
                description = fake.text(max_nb_chars=200)
                item_name = fake.bs().title() if feed_id % 4 == 0 else fake.catch_phrase()
                cta = random.choice(['Buy Now', 'Learn More', 'Register', 'View Details'])
                click_url = fake.url()
                items_data.append((feed_id, price, description, item_name, cta, click_url))

                # Log progress every 100 items
                if item_idx % 100 == 0:
                    print(f"Feed {feed_id}: {item_idx} items inserted.")

        cur.executemany("""
            INSERT INTO items (feed_id, price, description, name, cta, click_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, items_data)
        print("All items inserted.")

        # Step 5: Commit and close
        conn.commit()
        print("Database seeding completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()

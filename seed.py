import psycopg2
import random
import string

def generate_random_string(length=50):
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))

def main():
    # Database connection parameters
    db_params = {
        "dbname": "mydatabase",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": "5432"
    }

    # Feed types to randomly assign to each feed
    feed_types = ["news", "social", "entertainment", "sports", "technology", "business", "health", "travel", "food", "education"]

    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        print("Seeding database...")

        for feed_num in range(100):
            # Insert a feed
            feed_type = random.choice(feed_types)
            cursor.execute("INSERT INTO feeds (type) VALUES (%s) RETURNING id;", (feed_type,))
            feed_id = cursor.fetchone()[0]

            print(f"Feed {feed_num} with ID {feed_id} created.")

            # Insert 1000 items for this feed
            for item_num in range(1000):
                name = f"Item {item_num} in Feed {feed_id}"
                price = round(random.uniform(1.00, 100.00), 2)
                description = generate_random_string()

                cursor.execute("""
                    INSERT INTO items (feed_id, name, price, description)
                    VALUES (%s, %s, %s, %s)
                """, (feed_id, name, price, description))

            # Commit after each feed to prevent memory issues
            conn.commit()
            print(f"Feed {feed_num} with {1000} items seeded.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()

    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()

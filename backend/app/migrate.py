import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "retail_voice.db")

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}, skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if voice_session_id already exists in support_cases (idempotency check for migration)
        cursor.execute("PRAGMA table_info(support_cases)")
        columns = [row[1] for row in cursor.fetchall()]
        if "voice_session_id" in columns:
            print("Migration already applied.")
            return

        print("Running SQLite migration for support_cases table...")
        
        cursor.execute("PRAGMA foreign_keys=OFF")
        
        # 1. Rename old table
        cursor.execute("ALTER TABLE support_cases RENAME TO support_cases_old")
        
        # 2. Create new table
        cursor.execute("""
            CREATE TABLE support_cases (
                case_id VARCHAR(50) NOT NULL PRIMARY KEY,
                customer_id VARCHAR(20) NOT NULL,
                order_id VARCHAR(20),
                call_id VARCHAR(50),
                voice_session_id VARCHAR(50),
                category VARCHAR(50) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'pending',
                summary TEXT NOT NULL,
                requires_human_review BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                idempotency_key VARCHAR(50) UNIQUE,
                FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(call_id) REFERENCES call_records(call_id),
                FOREIGN KEY(voice_session_id) REFERENCES voice_support_sessions(session_id)
            )
        """)
        
        # 3. Copy old data
        cursor.execute("""
            INSERT INTO support_cases (
                case_id, customer_id, order_id, call_id, category, status, summary, 
                requires_human_review, created_at, updated_at
            )
            SELECT 
                case_id, customer_id, order_id, call_id, category, status, summary, 
                requires_human_review, created_at, updated_at
            FROM support_cases_old
        """)
        
        # 4. Drop old table
        cursor.execute("DROP TABLE support_cases_old")

        # 5. Create indexes
        cursor.execute("CREATE INDEX ix_support_cases_customer_id ON support_cases (customer_id)")
        cursor.execute("CREATE INDEX ix_support_cases_order_id ON support_cases (order_id)")
        cursor.execute("CREATE INDEX ix_support_cases_call_id ON support_cases (call_id)")
        cursor.execute("CREATE INDEX ix_support_cases_voice_session_id ON support_cases (voice_session_id)")
        
        cursor.execute("PRAGMA foreign_keys=ON")
        
        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()

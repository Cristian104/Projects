from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
            print("✅ Column 'role' added.")
        except Exception as e:
            print(f"⚠️ Column likely exists: {e}")

        # Replace 'jorg' with your actual username!
        conn.execute(text("UPDATE user SET role = 'dev' WHERE username = 'jorg'"))
        conn.commit()
        print("✅ Privileges updated.")

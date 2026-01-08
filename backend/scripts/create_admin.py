import asyncio
import argparse
import sys
import os

# Add backend to sys.path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole

async def promote_to_admin(identifier: str):
    async with AsyncSessionLocal() as db:
        # Try to find by social_id (Telegram ID) or username
        query = select(User)
        if identifier.isdigit():
            query = query.where(User.social_id == int(identifier))
        else:
            # Remove @ if present
            username = identifier.lstrip('@')
            query = query.where(User.username == username)
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User with identifier '{identifier}' not found in database.")
            print("Please ensure the user has logged in at least once via the Telegram bot.")
            return
        
        if user.role == UserRole.ADMIN:
            print(f"User {user.full_name} (@{user.username}) is already an ADMIN.")
            return

        user.role = UserRole.ADMIN
        await db.commit()
        print(f"Success: User {user.full_name} (@{user.username}) promoted to ADMIN.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote an existing user to admin.")
    parser.add_argument("identifier", help="Telegram ID or username (with or without @)")
    args = parser.parse_args()
    
    try:
        asyncio.run(promote_to_admin(args.identifier))
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

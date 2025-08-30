#!/usr/bin/env python3
"""
Clear Database Script
Removes all data from the database for local development
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal, engine


async def clear_database():
    """Clear all data from the database"""
    print("🗑️  Starting database cleanup...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get all table names
            result = await session.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT IN ('alembic_version')
                ORDER BY tablename
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("ℹ️  No tables found to clear")
                return
            
            print(f"📋 Found {len(tables)} tables to clear:")
            for table in tables:
                print(f"   - {table}")
            
            # Disable foreign key checks temporarily
            await session.execute(text("SET session_replication_role = replica;"))
            
            # Clear all tables
            for table in tables:
                try:
                    await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                    print(f"✅ Cleared table: {table}")
                except Exception as e:
                    print(f"⚠️  Warning clearing {table}: {e}")
            
            # Re-enable foreign key checks
            await session.execute(text("SET session_replication_role = DEFAULT;"))
            
            # Commit the changes
            await session.commit()
            
            print("✅ Database cleared successfully!")
            print("💡 You can now run the seed script to populate fresh data")
            
        except Exception as e:
            print(f"❌ Error during database cleanup: {e}")
            await session.rollback()
            raise


async def reset_sequences():
    """Reset all sequences to start from 1"""
    print("🔄 Resetting sequences...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get all sequence names
            result = await session.execute(text("""
                SELECT sequence_name FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
                ORDER BY sequence_name
            """))
            
            sequences = [row[0] for row in result.fetchall()]
            
            if sequences:
                print(f"📋 Found {len(sequences)} sequences to reset:")
                for seq in sequences:
                    print(f"   - {seq}")
                
                # Reset each sequence
                for seq in sequences:
                    try:
                        await session.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1;"))
                        print(f"✅ Reset sequence: {seq}")
                    except Exception as e:
                        print(f"⚠️  Warning resetting {seq}: {e}")
                
                await session.commit()
                print("✅ Sequences reset successfully!")
            else:
                print("ℹ️  No sequences found to reset")
                
        except Exception as e:
            print(f"❌ Error resetting sequences: {e}")
            await session.rollback()
            raise


async def main():
    """Main entry point"""
    print("🚀 Database Cleanup Tool")
    print("=" * 40)
    
    # Confirm action
    response = input("⚠️  This will DELETE ALL DATA from the database. Are you sure? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    # Double confirmation
    response2 = input("🔴 Type 'DELETE ALL' to confirm: ")
    if response2 != 'DELETE ALL':
        print("❌ Operation cancelled")
        return
    
    try:
        # Clear database
        await clear_database()
        
        # Reset sequences
        await reset_sequences()
        
        print("\n🎉 Database cleanup completed successfully!")
        print("💡 Next steps:")
        print("   1. Run: python scripts/seed.py")
        print("   2. Or run: make seed")
        
    except Exception as e:
        print(f"\n❌ Database cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

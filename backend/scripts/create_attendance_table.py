"""
Script to create attendance table if it doesn't exist.
This is needed when migrations were applied but table was not created.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    # Get database URL
    db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://admin:localdev_secret@db:5432/edu_platform')
    
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # Check if attendance table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'attendance'
            )
        """))
        exists = result.scalar()
        print(f'Attendance table exists: {exists}')
        
        if not exists:
            print('Creating attendance table...')
            
            # Create ENUM type if not exists
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE attendance_status_enum AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Create attendance table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id UUID DEFAULT gen_random_uuid() NOT NULL,
                    student_id UUID NOT NULL,
                    group_id UUID NOT NULL,
                    created_by UUID,
                    date DATE NOT NULL,
                    status attendance_status_enum DEFAULT 'ABSENT' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    PRIMARY KEY (id),
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT uq_attendance_student_date UNIQUE (student_id, date)
                )
            """))
            
            # Create index
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attendance_group_date ON attendance (group_id, date)
            """))
            
            # Create trigger function if not exists
            await conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            # Create trigger
            await conn.execute(text("""
                DROP TRIGGER IF EXISTS update_attendance_updated_at ON attendance
            """))
            await conn.execute(text("""
                CREATE TRIGGER update_attendance_updated_at 
                BEFORE UPDATE ON attendance 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """))
            
            print('Attendance table created successfully!')
        else:
            print('Attendance table already exists, no action needed.')
    
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())

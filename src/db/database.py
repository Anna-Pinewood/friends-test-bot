"""
Database operations for the bot using aiosqlite for async operations.
"""
import aiosqlite
import random
import json
from src.consts import DB_NAME, RESULT_RANGES


class Database:
    """Database class for handling all database operations."""

    def __init__(self):
        """Initialize database connection."""
        self.conn = None

    async def connect(self):
        """Connect to the database asynchronously."""
        self.conn = await aiosqlite.connect(DB_NAME)
        await self.create_tables()

    async def create_tables(self):
        """Create necessary tables if they don't exist."""
        # Users table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Tests table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            test_id TEXT PRIMARY KEY,
            user_id INTEGER,
            answers TEXT,  -- JSON string with question_id: answer_index
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        # Test results table
        await self.conn.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT,
            taker_id INTEGER,
            taker_username TEXT,
            score INTEGER,
            answers TEXT,  -- JSON string with question_id: answer_index
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES tests (test_id),
            FOREIGN KEY (taker_id) REFERENCES users (user_id)
        )
        ''')

        await self.conn.commit()

    async def add_user(self, user_id, username, first_name, last_name):
        """Add or update user in the database."""
        await self.conn.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        await self.conn.commit()

    async def create_test(self, user_id, answers):
        """Create a new test for a user."""
        # Generate a random test_id
        test_id = f"s_{random.randint(1000000000, 9999999999)}"

        # Store answers as JSON string
        answers_json = json.dumps(answers)

        # Insert into database
        await self.conn.execute('''
        INSERT INTO tests (test_id, user_id, answers)
        VALUES (?, ?, ?)
        ''', (test_id, user_id, answers_json))
        await self.conn.commit()

        return test_id

    async def get_test(self, test_id):
        """Get test details by test_id."""
        async with self.conn.execute('''
        SELECT t.user_id, t.answers, u.username, u.first_name, u.last_name
        FROM tests t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.test_id = ?
        ''', (test_id,)) as cursor:
            result = await cursor.fetchone()

            if not result:
                return None

            user_id, answers_json, username, first_name, last_name = result
            answers = json.loads(answers_json)

            return {
                'user_id': user_id,
                'answers': answers,
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            }

    async def save_test_result(self, test_id, taker_id, taker_username, answers):
        """Save the results of a test taken by a user."""
        # Get original test answers
        test_info = await self.get_test(test_id)
        if not test_info:
            return None

        original_answers = test_info['answers']

        # Calculate score
        correct_count = 0
        for q_id, original_answer_index in original_answers.items():
            taker_answer_index = answers.get(q_id)
            if taker_answer_index == original_answer_index:
                correct_count += 1

        total_questions = len(original_answers)
        percentage = round((correct_count / total_questions) * 100)

        # Determine status based on percentage
        status = None
        for (min_val, max_val), status_text in RESULT_RANGES.items():
            if min_val <= percentage <= max_val:
                status = status_text
                break

        # Store answers as JSON string
        answers_json = json.dumps(answers)

        # Save result to database
        await self.conn.execute('''
        INSERT INTO test_results (test_id, taker_id, taker_username, score, answers)
        VALUES (?, ?, ?, ?, ?)
        ''', (test_id, taker_id, taker_username, percentage, answers_json))
        await self.conn.commit()

        return {
            'percentage': percentage,
            'status': status,
            'creator': test_info
        }

    async def get_user_tests(self, user_id):
        """Get all tests created by a user."""
        async with self.conn.execute('''
        SELECT test_id, created_at
        FROM tests
        WHERE user_id = ?
        ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()

    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None


# Create a single instance of the database
db = Database()

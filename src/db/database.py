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
    
    async def get_test_statistics(self, user_id):
        """
        Get statistics for all tests created by a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: A dictionary with test statistics
        """
        # Get all tests created by the user
        async with self.conn.execute('''
        SELECT test_id
        FROM tests
        WHERE user_id = ?
        ORDER BY created_at DESC
        ''', (user_id,)) as cursor:
            tests = await cursor.fetchall()
        
        if not tests:
            return None
        
        # Initialize statistics
        stats = {
            'tests_count': len(tests),
            'total_passes': 0,
            'average_score': 0,
            'best_friends': [],
            'worst_friends': [],
            'detailed_tests': []
        }
        
        # Collect statistics for each test
        for test_row in tests:
            test_id = test_row[0]
            
            # Get test results
            async with self.conn.execute('''
            SELECT tr.taker_username, tr.score, tr.created_at
            FROM test_results tr
            WHERE tr.test_id = ?
            ORDER BY tr.score DESC
            ''', (test_id,)) as cursor:
                results = await cursor.fetchall()
            
            test_stats = {
                'test_id': test_id,
                'passes_count': len(results),
                'average_score': 0,
                'friends': []
            }
            
            if results:
                # Calculate average score for this test
                total_score = sum(result[1] for result in results)
                test_stats['average_score'] = round(total_score / len(results))
                
                # Add to global statistics
                stats['total_passes'] += len(results)
                
                # Add friends to test statistics
                for result in results:
                    username, score, created_at = result
                    test_stats['friends'].append({
                        'username': username,
                        'score': score,
                        'created_at': created_at
                    })
                
                # Add best and worst friends to global statistics
                if results and len(results) > 0:
                    best_friend = results[0]  # Already sorted by score DESC
                    stats['best_friends'].append({
                        'username': best_friend[0],
                        'score': best_friend[1],
                        'test_id': test_id
                    })
                    
                    worst_friend = results[-1]  # Last result with lowest score
                    stats['worst_friends'].append({
                        'username': worst_friend[0],
                        'score': worst_friend[1],
                        'test_id': test_id
                    })
            
            stats['detailed_tests'].append(test_stats)
        
        # Calculate overall average score
        if stats['total_passes'] > 0:
            total_all_scores = sum(test['average_score'] * test['passes_count'] for test in stats['detailed_tests'] if test['passes_count'] > 0)
            stats['average_score'] = round(total_all_scores / stats['total_passes'])
        
        # Sort best and worst friends
        stats['best_friends'] = sorted(stats['best_friends'], key=lambda x: x['score'], reverse=True)[:5]
        stats['worst_friends'] = sorted(stats['worst_friends'], key=lambda x: x['score'])[:5]
        
        return stats
    
    async def get_top_friends(self, limit=10):
        """
        Get top friends with highest average scores across all tests.
        
        Args:
            limit: Maximum number of friends to return
            
        Returns:
            list: List of friends with their average scores
        """
        async with self.conn.execute('''
        SELECT taker_username, AVG(score) as avg_score, COUNT(result_id) as passes_count
        FROM test_results
        GROUP BY taker_username
        HAVING passes_count > 0
        ORDER BY avg_score DESC
        LIMIT ?
        ''', (limit,)) as cursor:
            results = await cursor.fetchall()
        
        return [
            {
                'username': result[0],
                'average_score': round(result[1]),
                'passes_count': result[2]
            }
            for result in results
        ]
    
    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None


# Create a single instance of the database
db = Database()
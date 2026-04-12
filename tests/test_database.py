import unittest
import os
import uuid
from unittest.mock import patch

# We import the file so we can access its functions
import server.database as database

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        # Override the DB_PATH for testing
        self.test_db_path = 'test_users.db'
        self.patcher = patch('server.database.DB_PATH', self.test_db_path)
        self.patcher.start()
        
        # Initialize the test database with the needed schema
        database.initialize_db()
    
    def tearDown(self):
        # Stop tracking the mocked DB_PATH
        self.patcher.stop()
        
        # Clean up the test database file
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception as e:
                print(f"Cleanup error: {e}")

    def test_user_registration(self):
        success, msg = database.register_user('testuser', 'password123')
        self.assertTrue(success)
        self.assertEqual(msg, "Registration successful.")
        
        # Registering again should fail due to UNIQUE constraint constraint
        success_dup, msg_dup = database.register_user('testuser', 'password123')
        self.assertFalse(success_dup)
        self.assertEqual(msg_dup, "Username already exists.")

    def test_user_authentication(self):
        # Register a new user
        database.register_user('authuser', 'authpass123')
        
        # Good login
        success, msg = database.authenticate_user('authuser', 'authpass123')
        self.assertTrue(success)
        
        # Bad password
        success, msg = database.authenticate_user('authuser', 'wrongpass')
        self.assertFalse(success)
        
        # Non-existent user
        success, msg = database.authenticate_user('nobody', 'authpass123')
        self.assertFalse(success)

    def test_save_and_get_messages(self):
        # Prepare test data
        msg_id = str(uuid.uuid4())
        database.register_user('msguser', 'pass')
        
        # Save standard global message
        success = database.save_message(
            msg_id=msg_id,
            username='msguser',
            text='Hello world',
            msg_type='text',
            file_data=None,
            timestamp='12:00',
            group_id='global'
        )
        self.assertTrue(success)
        
        # Retrieve messages
        messages = database.get_messages(group_id='global', limit=10)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['text'], 'Hello world')
        self.assertEqual(messages[0]['username'], 'msguser')

    def test_create_and_join_group(self):
        database.register_user('groupcreator', 'pass')
        database.register_user('groupjoiner', 'pass')
        
        group_id = str(uuid.uuid4())
        success = database.create_group(group_id, 'Test Group', 'groupcreator')
        self.assertTrue(success)
        
        # Ensure creator is in the group auto-magically
        creator_groups = database.get_user_groups('groupcreator')
        self.assertTrue(any(g['id'] == group_id for g in creator_groups))
        
        # Test joining
        join_success = database.join_group(group_id, 'groupjoiner')
        self.assertTrue(join_success)
        
        # Verify joiner is part of group
        joiner_groups = database.get_user_groups('groupjoiner')
        self.assertTrue(any(g['id'] == group_id for g in joiner_groups))

if __name__ == '__main__':
    unittest.main()

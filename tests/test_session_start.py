"""
Tests for session_start.py - SessionStartDiscovery class
Following TDD: Write tests first, then implement
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
sys.path.insert(0, '/home/ndninja/scripts/tool_discovery')

from session_start import SessionStartDiscovery


class TestSessionStartDiscovery(unittest.TestCase):
    """Test SessionStartDiscovery functionality"""

    def setUp(self):
        """Set up test instance"""
        self.discovery = SessionStartDiscovery()

    def test_extract_topics_from_conversations(self):
        """Test extracting topics from conversation list"""
        conversations = [
            {
                'session_id': 'test-1',
                'topics_discussed': ['authentication', 'JWT tokens', 'API security']
            },
            {
                'session_id': 'test-2',
                'topics_discussed': ['database', 'PostgreSQL', 'indexing']
            },
            {
                'session_id': 'test-3',
                'topics_discussed': ['React', 'frontend', 'hooks']
            }
        ]

        topics = self.discovery.extract_topics(conversations)

        # Verify all topics extracted
        self.assertIsInstance(topics, list)
        self.assertIn('authentication', topics)
        self.assertIn('JWT tokens', topics)
        self.assertIn('database', topics)
        self.assertIn('PostgreSQL', topics)
        self.assertIn('React', topics)
        self.assertIn('hooks', topics)
        # Should have 9 topics total
        self.assertEqual(len(topics), 9)

    def test_extract_topics_handles_empty_list(self):
        """Test extract_topics handles empty conversation list"""
        conversations = []
        topics = self.discovery.extract_topics(conversations)
        self.assertEqual(topics, [])

    def test_extract_topics_handles_none_topics(self):
        """Test extract_topics handles None/null topics"""
        conversations = [
            {
                'session_id': 'test-1',
                'topics_discussed': None
            },
            {
                'session_id': 'test-2',
                'topics_discussed': ['database']
            }
        ]

        topics = self.discovery.extract_topics(conversations)
        self.assertIsInstance(topics, list)
        self.assertIn('database', topics)
        # Should only have 1 topic (null topics ignored)
        self.assertEqual(len(topics), 1)

    @patch('session_start.ToolDatabase')
    @patch('session_start.ToolScorer')
    def test_get_relevant_tools_with_topics(self, mock_scorer_class, mock_db_class):
        """Test get_relevant_tools returns list and respects limit"""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.connect.return_value = True

        # Mock cursor and conversations
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_db.conn = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate database returning conversations with topics
        mock_cursor.fetchall.return_value = [
            (['authentication', 'API'],),
            (['database', 'PostgreSQL'],),
        ]

        # Mock get_all_tools
        mock_db.get_all_tools.return_value = [
            {
                'key': 'jwt-helper',
                'data': {
                    'name': 'JWT Helper',
                    'command': 'jwt-decode',
                    'keywords': ['authentication', 'JWT', 'token']
                }
            },
            {
                'key': 'pg-admin',
                'data': {
                    'name': 'PostgreSQL Admin',
                    'command': 'pg-admin',
                    'keywords': ['database', 'PostgreSQL', 'SQL']
                }
            },
            {
                'key': 'api-tester',
                'data': {
                    'name': 'API Tester',
                    'command': 'api-test',
                    'keywords': ['API', 'HTTP', 'testing']
                }
            }
        ]

        # Mock scorer
        mock_scorer = MagicMock()
        mock_scorer_class.return_value = mock_scorer
        mock_scorer.rank_tools.return_value = [
            (mock_db.get_all_tools.return_value[0], 20),
            (mock_db.get_all_tools.return_value[1], 15)
        ]

        # Create a new discovery instance with mocked dependencies
        discovery = SessionStartDiscovery()

        # Test with limit=5
        result = discovery.get_relevant_tools(limit=5)

        # Verify returns list
        self.assertIsInstance(result, list)
        # Should have 2 tools (what scorer returned)
        self.assertEqual(len(result), 2)
        # Verify structure
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(len(result[0]), 2)  # (tool, score)

        # Test limit is passed to scorer
        mock_scorer.rank_tools.assert_called_once()
        call_args = mock_scorer.rank_tools.call_args
        self.assertEqual(call_args[1]['limit'], 5)

    @patch('session_start.ToolDatabase')
    def test_get_relevant_tools_handles_db_error(self, mock_db_class):
        """Test get_relevant_tools handles database errors gracefully"""
        # Mock database connection failure
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.connect.return_value = False

        # Create discovery instance AFTER patch is applied
        discovery = SessionStartDiscovery()
        result = discovery.get_relevant_tools(limit=5)

        # Should return empty list on error
        self.assertEqual(result, [])

    @patch('session_start.ToolDatabase')
    def test_get_relevant_tools_handles_exception(self, mock_db_class):
        """Test get_relevant_tools handles exceptions gracefully"""
        # Mock database raising exception
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.connect.side_effect = Exception("Database error")

        # Create discovery instance AFTER patch is applied
        discovery = SessionStartDiscovery()
        result = discovery.get_relevant_tools(limit=5)

        # Should return empty list on exception
        self.assertEqual(result, [])

    def test_format_suggestions(self):
        """Test format_suggestions includes name and command"""
        tools = [
            (
                {
                    'key': 'jwt-helper',
                    'data': {
                        'name': 'JWT Helper',
                        'command': 'jwt-decode',
                        'description': 'Decode JWT tokens',
                        'keywords': ['authentication']
                    }
                },
                20
            ),
            (
                {
                    'key': 'pg-admin',
                    'data': {
                        'name': 'PostgreSQL Admin',
                        'command': 'pg-admin',
                        'description': 'Manage PostgreSQL databases',
                        'keywords': ['database']
                    }
                },
                15
            )
        ]

        result = self.discovery.format_suggestions(tools)

        # Verify returns string
        self.assertIsInstance(result, str)
        # Verify includes tool names
        self.assertIn('JWT Helper', result)
        self.assertIn('PostgreSQL Admin', result)
        # Verify includes commands
        self.assertIn('jwt-decode', result)
        self.assertIn('pg-admin', result)
        # Verify includes scores
        self.assertIn('20', result)
        self.assertIn('15', result)

    def test_format_suggestions_empty_list(self):
        """Test format_suggestions handles empty list"""
        tools = []
        result = self.discovery.format_suggestions(tools)

        self.assertIsInstance(result, str)
        self.assertIn('No relevant tools', result)


if __name__ == '__main__':
    unittest.main()

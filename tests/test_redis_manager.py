import unittest
from unittest.mock import patch, MagicMock
import redis
from ttrpg_assistant.redis_manager.manager import RedisDataManager
from ttrpg_assistant.data_models.models import ContentChunk, SourceType
import numpy as np
import uuid

class TestRedisDataManager(unittest.TestCase):

    @patch('redis.Redis')
    def test_connect_success(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance

        # Act
        manager = RedisDataManager()

        # Assert
        self.assertIsNotNone(manager.redis_client)
        mock_redis.assert_called_once_with(host='localhost', port=6379, decode_responses=True)
        mock_redis_instance.ping.assert_called_once()

    @patch('redis.Redis')
    def test_connect_failure(self, mock_redis):
        # Arrange
        mock_redis.side_effect = redis.exceptions.ConnectionError

        # Act
        with self.assertRaises(redis.exceptions.ConnectionError):
            RedisDataManager()

    @patch('redis.Redis')
    def test_create_index_new(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis_instance.ft.return_value.info.side_effect = redis.exceptions.ResponseError
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        schema = [
            ("rulebook", "TEXT"),
            ("system", "TAG"),
            ("embedding", "VECTOR")
        ]
        index_name = "test_index"

        # Act
        manager.create_index(index_name, schema)

        # Assert
        mock_redis_instance.ft.assert_called_with(index_name)
        mock_redis_instance.ft().create_index.assert_called_once()

    @patch('redis.Redis')
    def test_create_index_exists(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        schema = [
            ("rulebook", "TEXT"),
            ("system", "TAG"),
            ("embedding", "VECTOR")
        ]
        index_name = "test_index"

        # Act
        manager.create_index(index_name, schema)

        # Assert
        mock_redis_instance.ft.assert_called_with(index_name)
        mock_redis_instance.ft().create_index.assert_not_called()

    @patch('redis.Redis')
    def test_store_rulebook_content(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis_instance.pipeline.return_value = mock_pipeline
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        chunks = [
            ContentChunk(id="1", rulebook="test", system="test", content_type="rule", title="Test Rule", content="This is a test rule.", page_number=1, section_path=["Chapter 1"], embedding=b"", metadata={}),
            ContentChunk(id="2", rulebook="test", system="test", content_type="spell", title="Test Spell", content="This is a test spell.", page_number=2, section_path=["Chapter 2"], embedding=b"", metadata={})
        ]
        index_name = "test_index"

        # Act
        manager.store_rulebook_content(index_name, chunks)

        # Assert
        self.assertEqual(mock_pipeline.hset.call_count, 2)
        mock_pipeline.execute.assert_called_once()

    @patch('redis.Redis')
    def test_vector_search(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        mock_doc = MagicMock()
        mock_doc.score = 0.9
        mock_doc.id = "test_index:1"
        mock_doc.rulebook = "test"
        mock_doc.system = "test"
        mock_doc.source_type = "rulebook"
        mock_doc.content_type = "rule"
        mock_doc.title = "Test Rule"
        mock_doc.content = "This is a test rule."
        mock_doc.page_number = "1"
        mock_doc.section_path = "['Chapter 1']"

        mock_redis_instance.ft.return_value.search.return_value.docs = [mock_doc]

        index_name = "test_index"
        query_embedding = np.array([0.1] * 384)

        # Act
        results = manager.vector_search(index_name, query_embedding, 1)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_chunk.id, "test_index:1")

    @patch('redis.Redis')
    def test_store_campaign_data(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        campaign_id = "test_campaign"
        data_type = "character"
        data = {"name": "Test Character"}

        # Act
        data_id = manager.store_campaign_data(campaign_id, data_type, data)

        # Assert
        self.assertIsNotNone(data_id)
        mock_redis_instance.hset.assert_called_once()

    @patch('redis.Redis')
    def test_get_campaign_data(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        campaign_id = "test_campaign"
        data_type = "character"

        mock_redis_instance.keys.return_value = ["campaign:test_campaign:character:1234"]
        mock_redis_instance.pipeline.return_value.execute.return_value = [{"name": "Test Character"}]

        # Act
        results = manager.get_campaign_data(campaign_id, data_type)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Test Character")

    @patch('redis.Redis')
    def test_update_campaign_data(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis_instance.exists.return_value = True
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        campaign_id = "test_campaign"
        data_type = "character"
        data_id = "1234"
        data = {"name": "Updated Character"}

        # Act
        success = manager.update_campaign_data(campaign_id, data_type, data_id, data)

        # Assert
        self.assertTrue(success)
        mock_redis_instance.hset.assert_called_once()

    @patch('redis.Redis')
    def test_delete_campaign_data(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis_instance.exists.return_value = True
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        campaign_id = "test_campaign"
        data_type = "character"
        data_id = "1234"

        # Act
        success = manager.delete_campaign_data(campaign_id, data_type, data_id)

        # Assert
        self.assertTrue(success)
        mock_redis_instance.delete.assert_called_once()

    @patch('redis.Redis')
    def test_store_rulebook_personality(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        rulebook_name = "test_rulebook"
        personality_text = "This is a test personality."

        # Act
        manager.store_rulebook_personality(rulebook_name, personality_text)

        # Assert
        mock_redis_instance.set.assert_called_once_with(f"personality:{rulebook_name}", personality_text)

    @patch('redis.Redis')
    def test_get_rulebook_personality(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()

        rulebook_name = "test_rulebook"

        # Act
        manager.get_rulebook_personality(rulebook_name)

        # Assert
        mock_redis_instance.get.assert_called_once_with(f"personality:{rulebook_name}")

if __name__ == '__main__':
    unittest.main()
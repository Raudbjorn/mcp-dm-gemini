import unittest
from unittest.mock import patch, MagicMock
from ttrpg_assistant.redis_manager.manager import RedisDataManager
import redis
from redis.commands.search.field import VectorField, TagField, TextField
from ttrpg_assistant.data_models.models import ContentChunk, SearchResult, CampaignData
import numpy as np
import json

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
        mock_redis.assert_called_once_with(
            host='localhost',
            port=6379,
            db=0,
            password=None,
            decode_responses=True
        )
        mock_redis_instance.ping.assert_called_once()

    @patch('redis.Redis')
    def test_connect_failure(self, mock_redis):
        # Arrange
        mock_redis.side_effect = redis.exceptions.ConnectionError

        # Act
        manager = RedisDataManager()

        # Assert
        self.assertIsNone(manager.redis_client)

    @patch('redis.Redis')
    def test_setup_vector_index_new(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis_instance.ft.return_value.info.side_effect = redis.exceptions.ResponseError
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()
        
        schema = [
            TextField("$.rulebook", as_name="rulebook"),
            TagField("$.system", as_name="system"),
            VectorField("$.embedding", "FLAT", {"TYPE": "FLOAT32", "DIM": 384, "DISTANCE_METRIC": "COSINE"}, as_name="vector")
        ]
        index_name = "test_index"

        # Act
        manager.setup_vector_index(index_name, schema)

        # Assert
        mock_redis_instance.ft.assert_called_with(index_name)
        mock_redis_instance.ft(index_name).create_index.assert_called_once()


    @patch('redis.Redis')
    def test_setup_vector_index_exists(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()
        
        schema = [
            TextField("$.rulebook", as_name="rulebook"),
            TagField("$.system", as_name="system"),
            VectorField("$.embedding", "FLAT", {"TYPE": "FLOAT32", "DIM": 384, "DISTANCE_METRIC": "COSINE"}, as_name="vector")
        ]
        index_name = "test_index"

        # Act
        manager.setup_vector_index(index_name, schema)

        # Assert
        mock_redis_instance.ft.assert_called_with(index_name)
        mock_redis_instance.ft(index_name).create_index.assert_not_called()

    @patch('ttrpg_assistant.redis_manager.manager.EmbeddingService')
    @patch('redis.Redis')
    def test_store_rulebook_content(self, mock_redis, mock_embedding_service):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis_instance.pipeline.return_value = mock_pipeline
        mock_redis.return_value = mock_redis_instance
        mock_embedding_service.return_value.generate_embedding.return_value = [0.1] * 384
        
        manager = RedisDataManager()
        
        chunks = [
            ContentChunk(id="1", rulebook="test", system="test", content_type="rule", title="Test Rule", content="This is a test rule.", page_number=1, section_path=["Chapter 1"], embedding=b"", metadata={}),
            ContentChunk(id="2", rulebook="test", system="test", content_type="spell", title="Test Spell", content="This is a test spell.", page_number=2, section_path=["Chapter 2"], embedding=b"", metadata={})
        ]
        index_name = "test_index"

        # Act
        manager.store_rulebook_content(index_name, chunks)

        # Assert
        self.assertEqual(mock_pipeline.json().set.call_count, 2)
        mock_pipeline.execute.assert_called_once()

    @patch('redis.Redis')
    def test_vector_search(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        manager = RedisDataManager()
        
        mock_doc = MagicMock()
        mock_doc.vector_score = 0.9
        mock_chunk = ContentChunk(id="1", rulebook="test", system="test", content_type="rule", title="Test Rule", content="This is a test rule.", page_number=1, section_path=["Chapter 1"], embedding=b"", metadata={})
        mock_doc.json = mock_chunk.model_dump_json()

        mock_redis_instance.ft.return_value.search.return_value.docs = [mock_doc]
        
        index_name = "test_index"
        query_embedding = np.array([0.1] * 384)

        # Act
        results = manager.vector_search(index_name, query_embedding)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results[0].relevance_score, 0.9)
        self.assertEqual(results[0].content_chunk.id, "1")

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
        mock_redis_instance.hgetall.return_value = {"name": "Test Character"}

        # Act
        results = manager.get_campaign_data(campaign_id, data_type)

        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Test Character")

    @patch('redis.Redis')
    def test_update_campaign_data(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()
        
        campaign_id = "test_campaign"
        data_type = "character"
        data_id = "1234"
        data = {"name": "Updated Character"}
        
        mock_redis_instance.exists.return_value = True
        mock_redis_instance.hget.return_value = "1"

        # Act
        result = manager.update_campaign_data(campaign_id, data_type, data_id, data)

        # Assert
        self.assertTrue(result)
        mock_redis_instance.hset.assert_called_once()

    @patch('redis.Redis')
    def test_delete_campaign_data(self, mock_redis):
        # Arrange
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        manager = RedisDataManager()
        
        campaign_id = "test_campaign"
        data_type = "character"
        data_id = "1234"
        
        mock_redis_instance.delete.return_value = 1

        # Act
        result = manager.delete_campaign_data(campaign_id, data_type, data_id)

        # Assert
        self.assertTrue(result)
        mock_redis_instance.delete.assert_called_once_with(f"campaign:{campaign_id}:{data_type}:{data_id}")

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
        mock_redis_instance.set.assert_called_once_with(f"rulebook_personality:{rulebook_name}", personality_text)

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
        mock_redis_instance.get.assert_called_once_with(f"rulebook_personality:{rulebook_name}")


if __name__ == '__main__':
    unittest.main()
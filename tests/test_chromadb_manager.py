import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from ttrpg_assistant.chromadb_manager.manager import ChromaDataManager
from ttrpg_assistant.data_models.models import ContentChunk, SearchResult
import numpy as np
import json


class TestChromaDataManager(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        
        # Create a test config file
        with open(self.config_path, 'w') as f:
            f.write("""
chromadb:
  persist_directory: "./test_chroma_db"
""")

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('chromadb.PersistentClient')
    def test_init_success(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Act
        manager = ChromaDataManager(
            config_path=str(self.config_path), 
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        
        # Assert
        self.assertIsNotNone(manager.client)
        mock_client.assert_called_once()

    @patch('chromadb.PersistentClient')
    def test_get_or_create_collection_new(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.get_collection.side_effect = ValueError("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        manager = ChromaDataManager(
            config_path=str(self.config_path),
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        
        # Act
        result = manager._get_or_create_collection("test_collection")
        
        # Assert
        self.assertEqual(result, mock_collection)
        mock_client_instance.create_collection.assert_called_with(
            name="test_collection",
            metadata={"hnsw:space": "cosine"}
        )

    @patch('chromadb.PersistentClient')
    def test_get_or_create_collection_existing(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        manager = ChromaDataManager(
            config_path=str(self.config_path),
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        
        # Act
        result = manager._get_or_create_collection("test_collection")
        
        # Assert
        self.assertEqual(result, mock_collection)
        mock_client_instance.get_collection.assert_called_with("test_collection")

    @patch('chromadb.PersistentClient')
    def test_store_campaign_data(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        manager = ChromaDataManager(
            config_path=str(self.config_path),
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        manager.campaign_collection = mock_collection
        
        test_data = {"name": "Test Character", "class": "Wizard"}
        
        # Act
        data_id = manager.store_campaign_data("test_campaign", "character", test_data)
        
        # Assert
        self.assertIsNotNone(data_id)
        mock_collection.upsert.assert_called_once()

    @patch('chromadb.PersistentClient')
    def test_get_campaign_data(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            'documents': ['{"name": "Test Character", "class": "Wizard"}'],
            'metadatas': [{"campaign_id": "test_campaign", "data_type": "character"}]
        }
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        manager = ChromaDataManager(
            config_path=str(self.config_path),
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        manager.campaign_collection = mock_collection
        
        # Act
        results = manager.get_campaign_data("test_campaign", "character", "test_id")
        
        # Assert
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Test Character")

    @patch('chromadb.PersistentClient')
    def test_vector_search(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'ids': [['test_id']],
            'documents': [['Test content']],
            'metadatas': [[{
                'rulebook': 'Test Rulebook',
                'system': 'Test System',
                'source_type': 'rulebook',
                'content_type': 'rule',
                'title': 'Test Rule',
                'page_number': 1,
                'section_path': '[]'
            }]],
            'distances': [[0.2]]
        }
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        manager = ChromaDataManager(
            config_path=str(self.config_path),
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        
        query_embedding = np.array([0.1, 0.2, 0.3])
        
        # Act
        results = manager.vector_search("test_index", query_embedding=query_embedding)
        
        # Assert
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results[0].content_chunk.title, "Test Rule")

    @patch('chromadb.PersistentClient')
    def test_store_and_get_personality(self, mock_client):
        # Arrange
        mock_client_instance = MagicMock()
        mock_personalities_collection = MagicMock()
        mock_personalities_collection.get.return_value = {
            'documents': ['Test personality for the rulebook']
        }
        mock_client_instance.get_collection.return_value = mock_personalities_collection
        mock_client.return_value = mock_client_instance
        
        manager = ChromaDataManager(
            config_path=str(self.config_path),
            persist_directory=str(Path(self.temp_dir) / "chroma_db")
        )
        
        # Act - Store
        manager.store_rulebook_personality("Test Rulebook", "Test personality for the rulebook")
        
        # Act - Retrieve
        personality = manager.get_rulebook_personality("Test Rulebook")
        
        # Assert
        mock_personalities_collection.upsert.assert_called_once()
        self.assertEqual(personality, "Test personality for the rulebook")


if __name__ == '__main__':
    unittest.main()
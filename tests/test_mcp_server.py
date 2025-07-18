import unittest
from fastapi.testclient import TestClient
from ttrpg_assistant.mcp_server.server import app
from ttrpg_assistant.mcp_server.dependencies import get_redis_manager, get_embedding_service, get_pdf_parser
from unittest.mock import MagicMock
from ttrpg_assistant.data_models.models import SearchResult, ContentChunk

class BaseMCPServerTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_redis_manager = MagicMock()
        self.mock_embedding_service = MagicMock()
        self.mock_pdf_parser = MagicMock()

        app.dependency_overrides[get_redis_manager] = lambda: self.mock_redis_manager
        app.dependency_overrides[get_embedding_service] = lambda: self.mock_embedding_service
        app.dependency_overrides[get_pdf_parser] = lambda: self.mock_pdf_parser

    def tearDown(self):
        app.dependency_overrides = {}

class TestMCPServer(BaseMCPServerTest):
    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "TTRPG Assistant MCP Server is running"})

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_search_rulebook(self):
        self.mock_embedding_service.generate_embedding.return_value = [0.1] * 384
        self.mock_redis_manager.vector_search.return_value = []

        response = self.client.post("/tools/search_rulebook", json={"query": "test"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    def test_manage_campaign_create(self):
        self.mock_redis_manager.store_campaign_data.return_value = "1234"

        response = self.client.post("/tools/manage_campaign", json={
            "action": "create",
            "campaign_id": "test_campaign",
            "data_type": "character",
            "data": {"name": "Test Character"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "data_id": "1234"})

    def test_manage_campaign_read(self):
        self.mock_redis_manager.get_campaign_data.return_value = [{"name": "Test Character"}]

        response = self.client.post("/tools/manage_campaign", json={
            "action": "read",
            "campaign_id": "test_campaign",
            "data_type": "character"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": [{"name": "Test Character"}]})

    def test_manage_campaign_update(self):
        self.mock_redis_manager.update_campaign_data.return_value = True

        response = self.client.post("/tools/manage_campaign", json={
            "action": "update",
            "campaign_id": "test_campaign",
            "data_type": "character",
            "data_id": "1234",
            "data": {"name": "Updated Character"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})

    def test_manage_campaign_delete(self):
        self.mock_redis_manager.delete_campaign_data.return_value = True

        response = self.client.post("/tools/manage_campaign", json={
            "action": "delete",
            "campaign_id": "test_campaign",
            "data_type": "character",
            "data_id": "1234"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})

    def test_manage_campaign_export(self):
        self.mock_redis_manager.export_campaign_data.return_value = {"character": [{"name": "Test Character"}]}

        response = self.client.post("/tools/manage_campaign", json={
            "action": "export",
            "campaign_id": "test_campaign"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": {"character": [{"name": "Test Character"}]}})

    def test_manage_campaign_import(self):
        response = self.client.post("/tools/manage_campaign", json={
            "action": "import",
            "campaign_id": "test_campaign",
            "data": {"character": [{"name": "Test Character"}]}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})
        self.mock_redis_manager.import_campaign_data.assert_called_once()


    def test_manage_campaign_invalid_action(self):
        response = self.client.post("/tools/manage_campaign", json={
            "action": "invalid",
            "campaign_id": "test_campaign",
            "data_type": "character"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Invalid action"})

    def test_manage_campaign_create_missing_data(self):
        response = self.client.post("/tools/manage_campaign", json={
            "action": "create",
            "campaign_id": "test_campaign",
            "data_type": "character"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Data and data_type are required for create action"})

    def test_manage_campaign_update_missing_data_id(self):
        response = self.client.post("/tools/manage_campaign", json={
            "action": "update",
            "campaign_id": "test_campaign",
            "data_type": "character",
            "data": {"name": "Updated Character"}
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Data ID, data, and data_type are required for update action"})

    def test_manage_campaign_delete_missing_data_id(self):
        response = self.client.post("/tools/manage_campaign", json={
            "action": "delete",
            "campaign_id": "test_campaign",
            "data_type": "character"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Data ID and data_type are required for delete action"})

    def test_add_rulebook(self):
        self.mock_pdf_parser.create_chunks.return_value = [
            {"id": "1", "text": "chunk 1", "page_number": 1, "section": {"title": "Title 1", "path": ["Title 1"]}},
            {"id": "2", "text": "chunk 2", "page_number": 2, "section": {"title": "Title 2", "path": ["Title 2"]}}
        ]
        self.mock_pdf_parser.extract_personality_text.return_value = "This is a test personality."

        response = self.client.post("/tools/add_rulebook", json={
            "pdf_path": "data/sample.pdf",
            "rulebook_name": "Test Rulebook",
            "system": "Test System"
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Rulebook 'Test Rulebook' added successfully."})
        self.mock_redis_manager.store_rulebook_content.assert_called_once()
        self.mock_redis_manager.store_rulebook_personality.assert_called_once_with("Test Rulebook", "This is a test personality.")

    def test_get_rulebook_personality(self):
        self.mock_redis_manager.get_rulebook_personality.return_value = "This is a test personality."

        response = self.client.post("/tools/get_rulebook_personality", json={"rulebook_name": "Test Rulebook"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"personality": "This is a test personality."})

    def test_get_rulebook_personality_not_found(self):
        self.mock_redis_manager.get_rulebook_personality.return_value = None

        response = self.client.post("/tools/get_rulebook_personality", json={"rulebook_name": "Test Rulebook"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Personality not found for this rulebook."})

    def test_get_character_creation_rules(self):
        mock_chunk = ContentChunk(id="1", rulebook="test", system="test", content_type="rule", title="Character Creation", content="These are the rules.", page_number=1, section_path=["Chapter 1"], embedding=b"", metadata={})
        mock_result = SearchResult(content_chunk=mock_chunk, relevance_score=0.9, match_type="semantic")
        self.mock_redis_manager.vector_search.return_value = [mock_result]

        response = self.client.post("/tools/get_character_creation_rules", json={"rulebook_name": "Test Rulebook"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"rules": "These are the rules."})

    def test_generate_backstory(self):
        self.mock_redis_manager.get_rulebook_personality.return_value = "This is a test personality."

        response = self.client.post("/tools/generate_backstory", json={
            "rulebook_name": "Test Rulebook",
            "character_details": {"name": "Test Character"}
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("backstory", response.json())

    def test_generate_npc(self):
        self.mock_redis_manager.get_rulebook_personality.return_value = "This is a test personality."
        self.mock_redis_manager.vector_search.return_value = []

        response = self.client.post("/tools/generate_npc", json={
            "rulebook_name": "Test Rulebook",
            "player_level": 1,
            "npc_description": "A friendly shopkeeper"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("npc", response.json())


if __name__ == '__main__':
    unittest.main()
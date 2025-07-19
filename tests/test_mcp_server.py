import unittest
from fastapi.testclient import TestClient
from ttrpg_assistant.mcp_server.server import app
from ttrpg_assistant.mcp_server.dependencies import get_redis_manager, get_embedding_service, get_pdf_parser
from unittest.mock import MagicMock, patch
from ttrpg_assistant.data_models.models import SearchResult, ContentChunk
import json
import os

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

    def test_search(self):
        self.mock_embedding_service.generate_embedding.return_value = [0.1] * 384
        self.mock_redis_manager.vector_search.return_value = []

        response = self.client.post("/tools/search", json={"query": "test"})
        
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

    # def test_add_source(self):
    #     self.mock_pdf_parser.create_chunks.return_value = [
    #         {"id": "1", "text": "chunk 1", "page_number": 1, "section": {"title": "Title 1", "path": ["Title 1"]}},
    #         {"id": "2", "text": "chunk 2", "page_number": 2, "section": {"title": "Title 2", "path": ["Title 2"]}}
    #     ]
    #     self.mock_pdf_parser.extract_personality_text.return_value = "This is a test personality."

    #     response = self.client.post("/tools/add_source", json={
    #         "pdf_path": "data/sample.pdf",
    #         "rulebook_name": "Test Rulebook",
    #         "system": "Test System"
    #     })

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json(), {"status": "success", "message": "Source 'Test Rulebook' added successfully."})
    #     self.mock_redis_manager.store_rulebook_content.assert_called_once()
    #     self.mock_redis_manager.store_rulebook_personality.assert_called_once_with("Test Rulebook", "This is a test personality.")

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

    def test_manage_session_start(self):
        self.mock_redis_manager.redis_client.exists.return_value = False
        response = self.client.post("/tools/manage_session", json={
            "action": "start",
            "campaign_id": "test_campaign",
            "session_id": "test_session"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Session started."})

    def test_manage_session_add_note(self):
        self.mock_redis_manager.redis_client.exists.return_value = True
        self.mock_redis_manager.redis_client.hgetall.return_value = {"notes": "[]"}
        response = self.client.post("/tools/manage_session", json={
            "action": "add_note",
            "campaign_id": "test_campaign",
            "session_id": "test_session",
            "data": {"note": "Test note"}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})

    def test_manage_session_set_initiative(self):
        self.mock_redis_manager.redis_client.exists.return_value = True
        self.mock_redis_manager.redis_client.hgetall.return_value = {"initiative_order": "[]"}
        response = self.client.post("/tools/manage_session", json={
            "action": "set_initiative",
            "campaign_id": "test_campaign",
            "session_id": "test_session",
            "data": {"order": [{"name": "Player 1", "initiative": 20}]}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})

    def test_manage_session_add_monster(self):
        self.mock_redis_manager.redis_client.exists.return_value = True
        self.mock_redis_manager.redis_client.hgetall.return_value = {"monsters": "[]"}
        response = self.client.post("/tools/manage_session", json={
            "action": "add_monster",
            "campaign_id": "test_campaign",
            "session_id": "test_session",
            "data": {"monster": {"name": "Goblin", "max_hp": 10, "current_hp": 10}}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})

    def test_manage_session_update_monster_hp(self):
        self.mock_redis_manager.redis_client.exists.return_value = True
        self.mock_redis_manager.redis_client.hgetall.return_value = {"monsters": json.dumps([{"name": "Goblin", "max_hp": 10, "current_hp": 10}])}
        response = self.client.post("/tools/manage_session", json={
            "action": "update_monster_hp",
            "campaign_id": "test_campaign",
            "session_id": "test_session",
            "data": {"name": "Goblin", "hp": 5}
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})

    def test_manage_session_get(self):
        self.mock_redis_manager.redis_client.exists.return_value = True
        self.mock_redis_manager.redis_client.hgetall.return_value = {
            "notes": "[\"Test note\"]",
            "initiative_order": "[{\"name\": \"Player 1\", \"initiative\": 20}]",
            "monsters": "[{\"name\": \"Goblin\", \"max_hp\": 10, \"current_hp\": 5}]"
        }
        response = self.client.post("/tools/manage_session", json={
            "action": "get",
            "campaign_id": "test_campaign",
            "session_id": "test_session"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("notes", response.json())

    def test_generate_map(self):
        response = self.client.post("/tools/generate_map", json={
            "rulebook_name": "Test Rulebook",
            "map_description": "A simple room"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("map", response.json())
        self.assertIn("<svg", response.json()["map"])

    @patch('ttrpg_assistant.mcp_server.tools.ContentPackager')
    def test_create_content_pack(self, mock_packager):
        response = self.client.post("/tools/create_content_pack", json={
            "source_name": "Test Source",
            "output_path": "data/test_pack.zip"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Content pack created at data/test_pack.zip"})
        mock_packager.return_value.create_pack.assert_called_once()

    @patch('ttrpg_assistant.mcp_server.tools.ContentPackager')
    def test_install_content_pack(self, mock_packager):
        mock_packager.return_value.load_pack.return_value = ([], "")
        response = self.client.post("/tools/install_content_pack", json={
            "pack_path": "data/test_pack.zip"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Content pack installed."})
        mock_packager.return_value.load_pack.assert_called_once()


if __name__ == '__main__':
    unittest.main()
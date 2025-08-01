import unittest
from ttrpg_assistant.embedding_service.embedding import EmbeddingService

class TestEmbeddingService(unittest.TestCase):

    def setUp(self):
        self.embedding_service = EmbeddingService()

    def test_generate_embedding(self):
        text = "This is a test sentence."
        embedding = self.embedding_service.generate_embedding(text)
        self.assertIsInstance(embedding, list)
        self.assertIsInstance(embedding[0], float)
        self.assertEqual(len(embedding), 384)

    def test_batch_embed(self):
        texts = ["This is the first sentence.", "This is the second sentence."]
        embeddings = self.embedding_service.batch_embed(texts)
        self.assertIsInstance(embeddings, list)
        self.assertIsInstance(embeddings[0], list)
        self.assertIsInstance(embeddings[0][0], float)
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), 384)

if __name__ == '__main__':
    unittest.main()

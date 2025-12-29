"""
Unit tests for EmbeddingService.

Tests embedding generation including:
- Single text embedding
- Batch embeddings
- Query+response embeddings
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.embedding_service import EmbeddingService, embedding_service


@pytest.mark.asyncio
class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    async def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        # Arrange
        text = "What is the weather today?"
        expected_embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions

        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=expected_embedding)]
            mock_client.embeddings.create.return_value = mock_response
            mock_client_method.return_value = mock_client

            # Act
            result = await embedding_service.generate_embedding(text)

            # Assert
            assert result == expected_embedding
            mock_client.embeddings.create.assert_called_once_with(
                model="text-embedding-3-small",
                input=text[:8000],
                encoding_format="float"
            )

    async def test_generate_embedding_with_empty_text(self):
        """Test embedding generation with empty text."""
        # Act
        result = await embedding_service.generate_embedding("")

        # Assert - should return zero vector
        assert len(result) == 1536
        assert all(x == 0.0 for x in result)

    async def test_generate_embedding_with_whitespace_only(self):
        """Test embedding generation with whitespace-only text."""
        # Act
        result = await embedding_service.generate_embedding("   \n\t  ")

        # Assert - should return zero vector
        assert len(result) == 1536
        assert all(x == 0.0 for x in result)

    async def test_generate_embedding_truncates_long_text(self):
        """Test that long text is truncated to 8000 chars."""
        # Arrange
        long_text = "a" * 10000  # 10k characters
        expected_embedding = [0.5] * 1536

        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=expected_embedding)]
            mock_client.embeddings.create.return_value = mock_response
            mock_client_method.return_value = mock_client

            # Act
            await embedding_service.generate_embedding(long_text)

            # Assert - verify text was truncated
            call_args = mock_client.embeddings.create.call_args
            assert len(call_args.kwargs['input']) == 8000

    async def test_generate_embedding_handles_api_error(self):
        """Test error handling when OpenAI API fails."""
        # Arrange
        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_client.embeddings.create.side_effect = Exception("API Error")
            mock_client_method.return_value = mock_client

            # Act
            result = await embedding_service.generate_embedding("test text")

            # Assert - should return zero vector on error
            assert len(result) == 1536
            assert all(x == 0.0 for x in result)

    async def test_generate_batch_embeddings_success(self):
        """Test successful batch embedding generation."""
        # Arrange
        texts = ["Text 1", "Text 2", "Text 3"]
        expected_embeddings = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536
        ]

        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [
                MagicMock(embedding=expected_embeddings[0]),
                MagicMock(embedding=expected_embeddings[1]),
                MagicMock(embedding=expected_embeddings[2])
            ]
            mock_client.embeddings.create.return_value = mock_response
            mock_client_method.return_value = mock_client

            # Act
            result = await embedding_service.generate_batch_embeddings(texts)

            # Assert
            assert len(result) == 3
            assert result == expected_embeddings
            mock_client.embeddings.create.assert_called_once()

    async def test_generate_batch_embeddings_with_empty_list(self):
        """Test batch embedding with empty list."""
        # Act
        result = await embedding_service.generate_batch_embeddings([])

        # Assert
        assert result == []

    async def test_generate_batch_embeddings_respects_batch_size(self):
        """Test that batch processing respects batch_size parameter."""
        # Arrange
        texts = [f"Text {i}" for i in range(150)]  # More than default batch_size
        expected_embedding = [0.1] * 1536

        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_response = MagicMock()
            # Return enough embeddings for each batch
            mock_response.data = [MagicMock(embedding=expected_embedding) for _ in range(100)]
            mock_client.embeddings.create.return_value = mock_response
            mock_client_method.return_value = mock_client

            # Act
            await embedding_service.generate_batch_embeddings(texts, batch_size=100)

            # Assert - should be called twice (100 + 50)
            assert mock_client.embeddings.create.call_count == 2

    async def test_generate_batch_embeddings_handles_error(self):
        """Test batch embedding error handling."""
        # Arrange
        texts = ["Text 1", "Text 2"]

        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_client.embeddings.create.side_effect = Exception("Batch error")
            mock_client_method.return_value = mock_client

            # Act
            result = await embedding_service.generate_batch_embeddings(texts)

            # Assert - should return zero vectors for all texts
            assert len(result) == 2
            assert all(len(emb) == 1536 for emb in result)
            assert all(all(x == 0.0 for x in emb) for emb in result)

    async def test_embed_query_and_response(self):
        """Test combined query+response embedding."""
        # Arrange
        query = "What is Python?"
        response = "Python is a programming language."
        expected_embedding = [0.7] * 1536

        with patch.object(embedding_service, '_ensure_client') as mock_client_method:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=expected_embedding)]
            mock_client.embeddings.create.return_value = mock_response
            mock_client_method.return_value = mock_client

            # Act
            result = await embedding_service.embed_query_and_response(query, response)

            # Assert
            assert result == expected_embedding

            # Verify combined text format
            call_args = mock_client.embeddings.create.call_args
            combined_text = call_args.kwargs['input']
            assert "Query:" in combined_text
            assert "Response:" in combined_text
            assert query in combined_text
            assert response in combined_text

    async def test_ensure_client_raises_error_without_api_key(self):
        """Test that _ensure_client raises error when API key is missing."""
        # Arrange
        service = EmbeddingService()

        with patch("app.services.embedding_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None

            # Act & Assert
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                service._ensure_client()

    async def test_ensure_client_lazy_loads(self):
        """Test that client is lazy loaded."""
        # Arrange
        service = EmbeddingService()
        assert service.client is None

        with patch("app.services.embedding_service.settings") as mock_settings, \
             patch("app.services.embedding_service.OpenAI") as mock_openai:

            mock_settings.OPENAI_API_KEY = "test_key"
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Act
            client1 = service._ensure_client()
            client2 = service._ensure_client()

            # Assert
            assert client1 is client2  # Should return same instance
            mock_openai.assert_called_once()  # Only called once

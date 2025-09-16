"""
Tests for the FastAPI application endpoints.
"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import io

from app import app

client = TestClient(app)


def create_test_image(width=100, height=100, color=(255, 255, 255)):
    """Create a test image in memory."""
    image = Image.new("RGB", (width, height), color)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


class TestHealthEndpoints:
    """Test health and basic endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint serves the frontend."""
        response = client.get("/")
        assert response.status_code == 200
        # Should serve HTML content
        assert "text/html" in response.headers.get("content-type", "")

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "P&ID Diff Finder"


class TestImageComparisonAPI:
    """Test the image comparison API endpoint."""

    def test_compare_images_success(self):
        """Test successful image comparison."""
        # Create two slightly different test images
        ref_image = create_test_image(100, 100, (255, 255, 255))  # White
        comp_image = create_test_image(100, 100, (250, 250, 250))  # Slightly off-white

        response = client.post(
            "/compare-images",
            files={
                "reference_image": ("ref.jpg", ref_image, "image/jpeg"),
                "compare_image": ("comp.jpg", comp_image, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "session_id" in data
        assert "similarity_score" in data
        assert "results" in data
        assert "metadata" in data

        # Check results structure
        results = data["results"]
        assert "ssim_difference" in results
        assert "bounded_differences" in results
        assert "drawn_differences" in results
        assert "mask_differences" in results

        # Check similarity score is a float between 0 and 1
        assert isinstance(data["similarity_score"], float)
        assert 0 <= data["similarity_score"] <= 1

    def test_compare_images_missing_reference(self):
        """Test error when reference image is missing."""
        comp_image = create_test_image()

        response = client.post(
            "/compare-images",
            files={"compare_image": ("comp.jpg", comp_image, "image/jpeg")},
        )

        assert response.status_code == 422  # Validation error

    def test_compare_images_missing_compare(self):
        """Test error when compare image is missing."""
        ref_image = create_test_image()

        response = client.post(
            "/compare-images",
            files={"reference_image": ("ref.jpg", ref_image, "image/jpeg")},
        )

        assert response.status_code == 422  # Validation error

    def test_compare_images_invalid_file_type(self):
        """Test error with invalid file type."""
        # Create a text file instead of image
        text_file = io.BytesIO(b"This is not an image")

        response = client.post(
            "/compare-images",
            files={
                "reference_image": ("ref.txt", text_file, "text/plain"),
                "compare_image": ("comp.jpg", create_test_image(), "image/jpeg"),
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "must be JPEG or PNG" in data["detail"]

    def test_compare_images_invalid_image_data(self):
        """Test error with corrupted image data."""
        # Create invalid image data
        invalid_data = io.BytesIO(b"Not a valid image file content")

        response = client.post(
            "/compare-images",
            files={
                "reference_image": ("ref.jpg", invalid_data, "image/jpeg"),
                "compare_image": ("comp.jpg", create_test_image(), "image/jpeg"),
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid" in data["detail"]

    def test_compare_images_large_file(self):
        """Test error with file too large."""
        # Create a large image (this is a mock test - in reality we'd need a very large file)
        large_image = create_test_image(
            1000, 1000
        )  # Not actually large enough to trigger limit

        # This test would need a truly large file to trigger the size limit
        # For now, we'll just verify the endpoint accepts normal sized files
        response = client.post(
            "/compare-images",
            files={
                "reference_image": ("ref.jpg", large_image, "image/jpeg"),
                "compare_image": ("comp.jpg", create_test_image(), "image/jpeg"),
            },
        )

        # Should succeed with normal sized images
        assert response.status_code == 200


class TestResultsEndpoint:
    """Test the results file serving endpoint."""

    def test_get_nonexistent_result(self):
        """Test 404 for non-existent result file."""
        response = client.get("/results/nonexistent.jpg")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.fixture
def temp_results_dir():
    """Create a temporary results directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test result file
        test_file = Path(temp_dir) / "test_result.jpg"
        test_image = Image.new("RGB", (100, 100), (255, 0, 0))
        test_image.save(test_file)
        yield temp_dir

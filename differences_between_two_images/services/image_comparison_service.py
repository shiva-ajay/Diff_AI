"""
Service module for image comparison operations via web API.
Integrates with the existing OpenCV-based image processing logic.
"""

import logging
import os
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Any
import cv2
import numpy as np
from dynaconf import settings

from differences_between_two_images.helpers import utils
from differences_between_two_images.helpers import exceptions

logger = logging.getLogger(__name__)


class ImageComparisonService:
    """Service class for handling image comparison operations."""

    def __init__(self):
        """Initialize the service with results directory."""
        self.results_dir = Path(settings.PATH_RESULTS)
        self.results_dir.mkdir(exist_ok=True)

    def compare_images(
        self, reference_image_data: bytes, compare_image_data: bytes
    ) -> Dict[str, Any]:
        """
        Compare two images and generate all difference visualizations.

        Args:
            reference_image_data: Bytes of the reference image
            compare_image_data: Bytes of the compare image

        Returns:
            Dictionary containing comparison results and file paths
        """
        session_id = str(uuid.uuid4())

        try:
            # Save uploaded images to temporary files
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as ref_temp:
                ref_temp.write(reference_image_data)
                ref_temp_path = ref_temp.name

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as comp_temp:
                comp_temp.write(compare_image_data)
                comp_temp_path = comp_temp.name

            # Process images using existing logic
            result = self._process_image_comparison(
                ref_temp_path, comp_temp_path, session_id
            )

            # Clean up temporary files
            os.unlink(ref_temp_path)
            os.unlink(comp_temp_path)

            return result

        except Exception as e:
            logger.error(f"Error comparing images: {str(e)}")
            # Clean up temporary files if they exist
            try:
                if "ref_temp_path" in locals():
                    os.unlink(ref_temp_path)
                if "comp_temp_path" in locals():
                    os.unlink(comp_temp_path)
            except:
                pass
            raise

    def _process_image_comparison(
        self, ref_path: str, comp_path: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Process image comparison using the existing OpenCV logic.

        Args:
            ref_path: Path to reference image
            comp_path: Path to compare image
            session_id: Unique session identifier

        Returns:
            Dictionary with comparison results
        """
        # Extract image matrices
        reference_frame = utils.extract_matrix_from_image(ref_path)
        compare_frame = utils.extract_matrix_from_image(comp_path)

        # Resize images to match dimensions if they differ
        if reference_frame.shape != compare_frame.shape:
            # Resize compare image to match reference image dimensions
            reference_height, reference_width = reference_frame.shape[:2]
            compare_frame = cv2.resize(
                compare_frame, (reference_width, reference_height)
            )
            logger.info(
                f"Resized compare image to match reference dimensions: {reference_frame.shape}"
            )

        # Convert to grayscale
        reference_gray = utils.convert_to_grayscale(reference_frame)
        compare_gray = utils.convert_to_grayscale(compare_frame)

        # Compute SSIM
        (similarity_score, diff) = utils.compute_ssim(reference_gray, compare_gray)
        logger.info(f"Similarity score: {similarity_score}")

        # Process difference image
        diff = utils.convert_image_to_8bit(diff)
        thresh = utils.binarize(diff)

        # Find contours
        contours = utils.find_contours(thresh.copy())

        # Prepare images for drawing
        reference_bounded = reference_frame.copy()
        compare_bounded = compare_frame.copy()
        compare_drawn = reference_frame.copy()
        mask = np.zeros(reference_frame.shape, dtype="uint8")

        # Process contours
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 40:  # Filter small noise
                # Add bounding boxes
                utils.bound_contour(reference_bounded, contour)
                utils.bound_contour(compare_bounded, contour)
                # Fill contours for mask and drawn differences
                utils.fill_contour(mask, contour)
                utils.fill_contour(compare_drawn, contour)

        # Generate result file paths
        result_files = {
            "ssim_difference": f"/results/{session_id}_ssim_difference.jpg",
            "bounded_differences": f"/results/{session_id}_bounded_differences.jpg",
            "drawn_differences": f"/results/{session_id}_drawn_differences.jpg",
            "mask_differences": f"/results/{session_id}_mask_differences.jpg",
        }

        # Save result images
        self._save_result_image(f"{session_id}_ssim_difference.jpg", thresh)
        self._save_result_image(
            f"{session_id}_bounded_differences.jpg", compare_bounded
        )
        self._save_result_image(f"{session_id}_drawn_differences.jpg", compare_drawn)
        self._save_result_image(f"{session_id}_mask_differences.jpg", mask)

        return {
            "session_id": session_id,
            "similarity_score": float(similarity_score),
            "results": result_files,
            "metadata": {
                "reference_shape": reference_frame.shape,
                "compare_shape": compare_frame.shape,
                "contours_found": len(contours),
                "significant_differences": len(
                    [c for c in contours if cv2.contourArea(c) > 40]
                ),
            },
        }

    def _save_result_image(self, filename: str, image: np.ndarray) -> None:
        """
        Save result image to the results directory.

        Args:
            filename: Name of the file to save
            image: Image array to save
        """
        filepath = self.results_dir / filename
        cv2.imwrite(str(filepath), image)
        logger.debug(f"Saved result image: {filepath}")

    def get_result_file_path(self, filename: str) -> Path:
        """
        Get the full path to a result file.

        Args:
            filename: Name of the result file

        Returns:
            Path object to the result file
        """
        return self.results_dir / filename

    def validate_image_data(self, image_data: bytes) -> bool:
        """
        Validate that the provided data is a valid image.

        Args:
            image_data: Bytes of the image to validate

        Returns:
            True if valid image, False otherwise
        """
        try:
            # Try to decode the image data
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img is not None
        except Exception as e:
            logger.warning(f"Image validation failed: {str(e)}")
            return False

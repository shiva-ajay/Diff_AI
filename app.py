"""
FastAPI application for P&ID Diff Finder.
Provides web interface for image difference detection using OpenCV.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from differences_between_two_images.services.image_comparison_service import (
    ImageComparisonService,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="P&ID Diff Finder",
    description="Compare images and pinpoint differences using OpenCV and SSIM",
    version="2.0.1",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
image_service = ImageComparisonService()

# Supported image types
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main HTML page."""
    try:
        html_path = Path("static/index.html")
        if html_path.exists():
            return FileResponse(html_path, media_type="text/html")
        else:
            # Return a basic HTML page if static file doesn't exist
            return HTMLResponse(
                """
            <!DOCTYPE html>
            <html>
            <head>
                <title>P&ID Diff Finder</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>P&ID Diff Finder</h1>
                <p>Static files not found. Please create static/index.html</p>
            </body>
            </html>
            """
            )
    except Exception as e:
        logger.error(f"Error serving root page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "P&ID Diff Finder", "version": "2.0.1"}


@app.post("/compare-images")
async def compare_images(
    reference_image: UploadFile = File(..., description="Reference image file"),
    compare_image: UploadFile = File(
        ..., description="Image to compare against reference"
    ),
) -> Dict[str, Any]:
    """
    Compare two images and return difference analysis.

    Args:
        reference_image: The reference image file
        compare_image: The image to compare against the reference

    Returns:
        Dictionary containing comparison results and file paths
    """
    try:
        # Validate file types
        if reference_image.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Reference image must be JPEG or PNG. Got: {reference_image.content_type}",
            )

        if compare_image.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Compare image must be JPEG or PNG. Got: {compare_image.content_type}",
            )

        # Read file contents
        reference_data = await reference_image.read()
        compare_data = await compare_image.read()

        # Validate file sizes
        if len(reference_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Reference image too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB",
            )

        if len(compare_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Compare image too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB",
            )

        # Validate image data
        if not image_service.validate_image_data(reference_data):
            raise HTTPException(status_code=400, detail="Invalid reference image data")

        if not image_service.validate_image_data(compare_data):
            raise HTTPException(status_code=400, detail="Invalid compare image data")

        # Process images
        logger.info(
            f"Processing image comparison: {reference_image.filename} vs {compare_image.filename}"
        )
        result = image_service.compare_images(reference_data, compare_data)

        logger.info(f"Comparison completed. Session ID: {result['session_id']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image comparison: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during image processing"
        )


@app.get("/results/{filename}")
async def get_result_file(filename: str) -> FileResponse:
    """
    Serve result image files.

    Args:
        filename: Name of the result file to serve

    Returns:
        FileResponse with the requested image
    """
    try:
        file_path = image_service.get_result_file_path(filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Result file not found")

        # Determine media type based on file extension
        media_type = "image/jpeg"
        if filename.lower().endswith(".png"):
            media_type = "image/png"

        return FileResponse(file_path, media_type=media_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving result file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom 404 handler."""
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=404, content={"detail": "Endpoint not found"})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom 500 handler."""
    from fastapi.responses import JSONResponse

    logger.error(f"Internal server error: {request.url}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    # Run the application
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

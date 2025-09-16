# P&ID Diff Finder - Image Difference Detection

A modern web application for detecting and visualizing differences between images using OpenCV and the SSIM (Structural Similarity Index) method. Features both a command-line interface and a user-friendly web interface.

## 🌟 Features

- **Modern Web Interface**: Clean, responsive UI with drag-and-drop file uploads
- **Multiple Visualization Types**:
  - SSIM Difference analysis
  - Bounded differences with rectangles
  - Drawn differences with filled contours
  - Binary mask visualization
- **Real-time Processing**: Progress indicators and instant results
- **Production Ready**: FastAPI backend with comprehensive error handling
- **Command Line Support**: Original CLI functionality preserved

## Versions

The latest version of this project is currently `2.0.1`.

**Note:** to navigate through the different versions, use e.g. `git checkout tags/1.0.1`.

## Dependencies

To manage the dependencies, I recommend using the python package manager `poetry`. You might have to install it before using `brew install poetry` (on MacOS).

Then, just install the different dependencies:

    poetry update

**Note:** In case you want to use any other methods, a `requirements.txt` file is also provided.

## 🚀 Quick Start

### Web Application (Recommended)

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Start the web server:

   ```bash
   poetry run python app.py
   ```

3. Open your browser and navigate to: `http://localhost:8000`

4. Upload your reference and compare images using the drag-and-drop interface

5. Click "Find Differences" to see the analysis results

### Command Line Interface

Once the virtual environment is set up, you can use the original CLI:

On MacOS:

```bash
poetry run main -bd -dd -dm -ds image1.jpg image2.jpg
```

On Windows PowerShell:

```bash
poetry run main -bd -dd -dm -ds image1.jpg image2.jpg
```

**CLI Options:**

- `-dm` / `--draw-mask`: Generate mask differences
- `-bd` / `--bound-differences`: Highlight differences with rectangles
- `-dd` / `--draw-differences`: Fill and highlight differences
- `-ds` / `--display-ssim`: Show SSIM difference analysis
- `-p` / `--popup`: Display results in popup windows

**Notes:**

- The first image is used as the reference for comparison
- Results are saved in the `results/` folder
- Web interface provides all visualization types automatically

### Example

    poetry run main -bd -dd -dm -ds dataset/image-1.jpg dataset/image-2.jpg

## 🏗️ Web Application Architecture

The web application consists of:

### Backend (FastAPI)

- **FastAPI Application** (`app.py`): Main web server with REST API endpoints
- **Image Comparison Service** (`differences_between_two_images/services/image_comparison_service.py`): Core image processing logic
- **Existing OpenCV Module** (`differences_between_two_images/`): Original image processing algorithms

### Frontend

- **Modern HTML5 Interface** (`static/index.html`): Responsive design with drag-and-drop uploads
- **CSS3 Styling** (`static/styles.css`): Modern, clean visual design
- **JavaScript** (`static/script.js`): File handling, API communication, and UI interactions

### API Endpoints

- `GET /`: Serves the web interface
- `GET /health`: Health check endpoint
- `POST /compare-images`: Main image comparison endpoint
- `GET /results/{filename}`: Serves generated result images

## Back-end logic explained

Let's take the following images:

![](sprites/image-1.jpg)

and:

![](sprites/image-2.jpg)

The first step to do is to compute the ssim difference after having had converted the images from colorized to gray-scaled:

![](sprites/ssim.jpg)

Then, we isolate the differences by binarizing the image:

![](sprites/differences.jpg)

Then, we remove the noise by applying a mask and removing the outliers i.e. the freckles for which the surface is inferior to an arbitrary number:

![](sprites/mask.jpg)

Finally, we compute the bouding box for each surface and superpose it to the image:

![](sprites/boxed.jpg)

## Troubleshooting

If you encounter a similar error when applying `pylint`, e.g.:

    E1101: Module 'cv2' has no 'imread' member (no-member)

Then, edit the following line in the `.pylintrc` for:

    generated-members=["cv2.*"]

If you encounter the following, related to the use of `click`:

    E1120: No value for argument 'images' in function call (no-value-for-parameter)

Then, edit the following line in the `.pylintrc` for:

    signature-mutators=click.decorators.option

## Inspirations

- https://stackoverflow.com/questions/56183201/detect-and-visualize-differences-between-two-images-with-opencv-python
- https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf

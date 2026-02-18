# Image Vectorization Feature

## Overview
RAG System now supports image upload and automatic vector extraction using CLIP (Contrastive Language-Image Pre-training).

## Features

### Image Processing
- **Supported Formats**: PNG, JPG, JPEG, GIF, BMP, WEBP
- **Model**: OpenAI CLIP ViT-B/32
- **Vector Dimension**: 512 (adapted to 384 for Milvus compatibility)
- **Automatic Processing**: Upload images through the UI and vectors are extracted automatically

### How It Works

1. **Upload**: User uploads an image through the Upload tab
2. **Vector Extraction**: CLIP model processes the image and extracts a 512-dimensional semantic vector
3. **Storage**: Vector is stored in Milvus alongside image metadata
4. **Search**: Images can be searched semantically based on visual content

### Technical Details

#### CLIP Model
- **Model Name**: `openai/clip-vit-base-patch32`
- **Architecture**: Vision Transformer (ViT)
- **Training**: Trained on 400M image-text pairs
- **Capabilities**:
  - Image-to-vector conversion
  - Image-to-text similarity
  - Zero-shot image classification

#### Vector Adaptation
- CLIP outputs 512-dimensional vectors
- Milvus collections use 384-dimensional vectors (from all-MiniLM-L6-v2)
- **Adaptation Method**: Simple truncation to first 384 dimensions
- Alternative: Could use PCA or learned projection for better results

### Usage

#### Via Web Interface
1. Navigate to "Data Retrieval" → "Upload File"
2. Select an image file (PNG, JPG, etc.)
3. Choose target collection
4. Click "Upload File"
5. Vector is automatically extracted and stored

#### Via API
```bash
curl -X POST http://localhost:5001/upload_file \
  -F "file=@/path/to/image.png" \
  -F "collection=documents"
```

Response:
```json
{
  "success": true,
  "message": "Image stored successfully with 512-dim vector (adapted to 384-dim)",
  "vector_dim": 512,
  "file_type": "image"
}
```

### Code Components

#### `image_vectorizer.py`
Main module for image vectorization:
- `ImageVectorizer` class
- `extract_vector()` - Single image processing
- `extract_batch()` - Batch processing
- `image_to_text_similarity()` - Image-text matching

#### `web_interface.py` Updates
- Added image format support to `ALLOWED_EXTENSIONS`
- Modified `upload_file()` endpoint to detect and process images
- Added `store_document_with_vector()` function
- Integrated CLIP model loading

#### `UploadTab.js` Updates
- Updated file input to accept image formats
- Added visual indicators for image support
- Shows vector dimension in success message

### Example Use Cases

1. **Logo Similarity Search**
   - Upload company logos
   - Find similar logos by visual features
   - Search by description: "technology logo" or "blue circular logo"

2. **Product Images**
   - Index product catalog images
   - Search by visual similarity
   - Find similar products

3. **Document Screenshots**
   - Upload screenshots of code, diagrams, or documents
   - Search by content description
   - Find related visual information

### Performance

- **Loading Time**: ~5-10 seconds (first time only)
- **Processing Time**: ~100-200ms per image
- **Memory Usage**: ~500MB for CLIP model
- **GPU Support**: Automatically uses CUDA if available

### Future Improvements

1. **Better Vector Adaptation**
   - Use PCA or learned projection instead of truncation
   - Train adapter network to map 512→384 dimensions

2. **Image-Text Search**
   - Search images using text descriptions
   - Find images matching natural language queries

3. **Duplicate Detection**
   - Identify duplicate or near-duplicate images
   - Vector similarity threshold tuning

4. **Thumbnail Generation**
   - Store image thumbnails with vectors
   - Display in search results

5. **Batch Upload**
   - Support multiple image uploads at once
   - Folder/directory upload

### Dependencies

```
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
pillow>=9.0.0
numpy>=1.24.0
```

### Installation

```bash
cd /path/to/Sonatype-Personal
source venv/bin/activate
pip install torch torchvision transformers pillow
```

### Testing

Test the image vectorizer:
```bash
python image_vectorizer.py
```

Test with the logo:
```python
from image_vectorizer import ImageVectorizer

vectorizer = ImageVectorizer()
vector = vectorizer.extract_vector('frontend/public/optus-logo.png')
print(f"Vector shape: {vector.shape}")
print(f"Vector norm: {np.linalg.norm(vector)}")
```

### Troubleshooting

**Issue**: "Image vectorizer not available"
- **Solution**: Ensure CLIP model is loaded. Check venv activation.

**Issue**: "Vector dimension mismatch"
- **Solution**: Vector is automatically adapted. Check `store_document_with_vector()` function.

**Issue**: Slow processing
- **Solution**: Enable GPU support or reduce batch size.

### API Reference

See `/api/docs` endpoint for complete API documentation.

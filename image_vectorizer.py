#!/usr/bin/env python3
"""
Image Vectorization Module
Extract embeddings from images using CLIP model
"""

import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import numpy as np
from typing import Union, List
import os

class ImageVectorizer:
    """Extract semantic vectors from images using CLIP"""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize CLIP model for image vectorization

        Args:
            model_name: Hugging Face model name (default: CLIP ViT-B/32)
        """
        print(f"Loading CLIP model: {model_name}")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()
        print(f"✓ CLIP model loaded on {self.device}")

    def extract_vector(self, image_path: str) -> np.ndarray:
        """
        Extract embedding vector from a single image

        Args:
            image_path: Path to image file

        Returns:
            numpy array of shape (512,) - normalized embedding vector
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load and preprocess image
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        # Extract features
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)

        # Normalize and convert to numpy
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        vector = image_features.cpu().numpy().squeeze()

        return vector

    def extract_batch(self, image_paths: List[str]) -> np.ndarray:
        """
        Extract embeddings from multiple images in batch

        Args:
            image_paths: List of image file paths

        Returns:
            numpy array of shape (N, 512) - normalized embedding vectors
        """
        images = []
        for path in image_paths:
            if not os.path.exists(path):
                print(f"Warning: Image not found: {path}")
                continue
            images.append(Image.open(path).convert("RGB"))

        if not images:
            raise ValueError("No valid images found")

        # Process batch
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)

        # Extract features
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)

        # Normalize and convert to numpy
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        vectors = image_features.cpu().numpy()

        return vectors

    def get_embedding_dim(self) -> int:
        """Return the dimensionality of embeddings (512 for CLIP ViT-B/32)"""
        return self.model.config.projection_dim

    def image_to_text_similarity(self, image_path: str, texts: List[str]) -> np.ndarray:
        """
        Compute similarity between an image and multiple text descriptions

        Args:
            image_path: Path to image file
            texts: List of text descriptions

        Returns:
            numpy array of similarity scores (0-1)
        """
        image = Image.open(image_path).convert("RGB")

        inputs = self.processor(
            text=texts,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        return probs.cpu().numpy().squeeze()


def test_vectorizer():
    """Test the image vectorizer"""
    vectorizer = ImageVectorizer()

    print(f"\nEmbedding dimension: {vectorizer.get_embedding_dim()}")

    # Test with logo if it exists
    logo_path = "frontend/public/optus-logo.png"
    if os.path.exists(logo_path):
        print(f"\nTesting with {logo_path}")
        vector = vectorizer.extract_vector(logo_path)
        print(f"✓ Vector shape: {vector.shape}")
        print(f"✓ Vector norm: {np.linalg.norm(vector):.4f}")
        print(f"✓ Sample values: {vector[:5]}")

        # Test similarity with descriptions
        descriptions = [
            "A logo for artificial intelligence",
            "A business logo",
            "A technology brand",
            "A food product",
            "An abstract art piece"
        ]
        similarities = vectorizer.image_to_text_similarity(logo_path, descriptions)
        print("\n📊 Image-Text Similarities:")
        for desc, score in zip(descriptions, similarities):
            print(f"  {desc}: {score:.3f}")
    else:
        print(f"Logo not found at {logo_path}")


if __name__ == "__main__":
    test_vectorizer()

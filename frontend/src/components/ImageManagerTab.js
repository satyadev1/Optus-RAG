import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Button,
  Input,
  Textarea,
  Text,
  Image,
  useColorMode,
  Icon,
  Badge,
  SimpleGrid,
  Spinner,
  Alert,
  AlertIcon,
  FormControl,
  FormLabel,
  Tooltip,
} from '@chakra-ui/react';
import { FiUpload, FiSearch, FiImage, FiDownload } from 'react-icons/fi';
import axios from 'axios';

function ImageManagerTab() {
  const { colorMode } = useColorMode();
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageName, setImageName] = useState('');
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [retrievedImages, setRetrievedImages] = useState([]);
  const [topK, setTopK] = useState(3);

  const bgColor = colorMode === 'dark' ? 'rgba(30,58,95,0.3)' : 'rgba(255,255,255,0.5)';
  const borderColor = colorMode === 'dark' ? 'rgba(77,124,178,0.3)' : 'rgba(77,124,178,0.2)';

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImageName(file.name);

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveImage = async () => {
    if (!imagePreview) {
      setUploadMessage('Please select an image first');
      return;
    }

    setIsUploading(true);
    setUploadMessage('');

    try {
      const response = await axios.post('/save_image', {
        image_data: imagePreview,
        name: imageName || `screenshot_${Date.now()}.png`,
        description: description || 'No description provided'
      });

      if (response.data.success) {
        setUploadMessage(`✅ ${response.data.message}`);
        // Clear form
        setImageFile(null);
        setImagePreview(null);
        setImageName('');
        setDescription('');
      } else {
        setUploadMessage(`❌ ${response.data.message}`);
      }
    } catch (error) {
      setUploadMessage(`❌ Error: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearchImages = async () => {
    if (!searchQuery.trim()) {
      return;
    }

    setIsSearching(true);
    setRetrievedImages([]);

    try {
      const response = await axios.post('/retrieve_image', {
        query: searchQuery,
        top_k: topK
      });

      if (response.data.success) {
        setRetrievedImages(response.data.images);
      }
    } catch (error) {
      console.error('Error searching images:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleDownloadImage = (imageData, title) => {
    const link = document.createElement('a');
    link.href = imageData;
    link.download = title;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box
          backdropFilter="blur(8px)"
          background={bgColor}
          border="1px solid"
          borderColor={borderColor}
          borderRadius="20px"
          p={6}
        >
          <Text fontSize="2xl" fontWeight="700" color={colorMode === 'dark' ? 'white' : '#1e293b'} mb={2}>
            📸 Image Manager
          </Text>
          <Text fontSize="sm" color={colorMode === 'dark' ? 'rgba(179,217,255,0.9)' : 'rgba(77,124,178,0.8)'}>
            Save images with AI-powered embeddings and retrieve them using natural language queries
          </Text>
        </Box>

        {/* Upload Section */}
        <Box
          backdropFilter="blur(8px)"
          background={bgColor}
          border="1px solid"
          borderColor={borderColor}
          borderRadius="20px"
          p={6}
        >
          <HStack spacing={2} mb={4}>
            <Icon as={FiUpload} color={colorMode === 'dark' ? '#7ba8d1' : '#4d7cb2'} />
            <Text fontSize="lg" fontWeight="600">
              Save Image
            </Text>
          </HStack>

          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel fontSize="sm">Select Image</FormLabel>
              <Input
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                size="md"
                p={1}
              />
            </FormControl>

            {imagePreview && (
              <Box
                border="2px solid"
                borderColor={borderColor}
                borderRadius="12px"
                p={4}
                bg={colorMode === 'dark' ? 'rgba(0,0,0,0.2)' : 'rgba(248,250,252,0.5)'}
              >
                <Image
                  src={imagePreview}
                  alt="Preview"
                  maxH="300px"
                  objectFit="contain"
                  mx="auto"
                  borderRadius="8px"
                />
              </Box>
            )}

            <FormControl>
              <FormLabel fontSize="sm">Image Name</FormLabel>
              <Input
                value={imageName}
                onChange={(e) => setImageName(e.target.value)}
                placeholder="Enter image name"
                size="md"
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Description (helps with retrieval)</FormLabel>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what's in the image..."
                rows={3}
                size="md"
              />
            </FormControl>

            <Button
              leftIcon={<FiImage />}
              colorScheme="blue"
              onClick={handleSaveImage}
              isLoading={isUploading}
              loadingText="Saving..."
              isDisabled={!imagePreview}
              size="lg"
            >
              Save Image to Milvus DB
            </Button>

            {uploadMessage && (
              <Alert
                status={uploadMessage.startsWith('✅') ? 'success' : 'error'}
                borderRadius="12px"
              >
                <AlertIcon />
                {uploadMessage}
              </Alert>
            )}
          </VStack>
        </Box>

        {/* Search Section */}
        <Box
          backdropFilter="blur(8px)"
          background={bgColor}
          border="1px solid"
          borderColor={borderColor}
          borderRadius="20px"
          p={6}
        >
          <HStack spacing={2} mb={4}>
            <Icon as={FiSearch} color={colorMode === 'dark' ? '#7ba8d1' : '#4d7cb2'} />
            <Text fontSize="lg" fontWeight="600">
              Retrieve Images
            </Text>
          </HStack>

          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel fontSize="sm">Search Query</FormLabel>
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Describe the image you're looking for..."
                size="md"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') handleSearchImages();
                }}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Number of Results</FormLabel>
              <Input
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                min={1}
                max={10}
                size="md"
                w="120px"
              />
            </FormControl>

            <Button
              leftIcon={<FiSearch />}
              colorScheme="blue"
              onClick={handleSearchImages}
              isLoading={isSearching}
              loadingText="Searching..."
              isDisabled={!searchQuery.trim()}
              size="lg"
            >
              Search Images
            </Button>
          </VStack>
        </Box>

        {/* Results */}
        {isSearching && (
          <Box textAlign="center" py={8}>
            <Spinner size="xl" color="blue.600" thickness="4px" />
            <Text mt={4}>Searching for images...</Text>
          </Box>
        )}

        {!isSearching && retrievedImages.length > 0 && (
          <Box
            backdropFilter="blur(8px)"
            background={bgColor}
            border="1px solid"
            borderColor={borderColor}
            borderRadius="20px"
            p={6}
          >
            <Text fontSize="lg" fontWeight="600" mb={4}>
              Found {retrievedImages.length} Image{retrievedImages.length !== 1 ? 's' : ''}
            </Text>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {retrievedImages.map((img, idx) => (
                <Box
                  key={idx}
                  border="1px solid"
                  borderColor={borderColor}
                  borderRadius="12px"
                  p={4}
                  bg={colorMode === 'dark' ? 'rgba(0,0,0,0.2)' : 'rgba(248,250,252,0.5)'}
                  transition="all 200ms"
                  _hover={{
                    borderColor: colorMode === 'dark' ? 'rgba(77,124,178,0.6)' : 'rgba(77,124,178,0.5)',
                    transform: 'translateY(-2px)',
                  }}
                >
                  <Image
                    src={img.image_data}
                    alt={img.title}
                    borderRadius="8px"
                    mb={3}
                    maxH="200px"
                    objectFit="contain"
                    w="100%"
                  />

                  <VStack align="stretch" spacing={2}>
                    <Text fontWeight="600" fontSize="sm" noOfLines={1}>
                      {img.title}
                    </Text>

                    <Text fontSize="xs" color="gray.500" noOfLines={2}>
                      {img.description}
                    </Text>

                    <HStack justify="space-between">
                      <Badge colorScheme="blue" fontSize="2xs">
                        Score: {(1 - img.score).toFixed(3)}
                      </Badge>
                      <Badge colorScheme="green" fontSize="2xs">
                        {img.width} × {img.height}
                      </Badge>
                    </HStack>

                    <Tooltip label="Download Image">
                      <Button
                        size="sm"
                        leftIcon={<FiDownload />}
                        colorScheme="blue"
                        variant="outline"
                        onClick={() => handleDownloadImage(img.image_data, img.title)}
                      >
                        Download
                      </Button>
                    </Tooltip>
                  </VStack>
                </Box>
              ))}
            </SimpleGrid>
          </Box>
        )}

        {!isSearching && retrievedImages.length === 0 && searchQuery && (
          <Alert status="info" borderRadius="20px">
            <AlertIcon />
            No images found. Try a different search query.
          </Alert>
        )}
      </VStack>
    </Box>
  );
}

export default ImageManagerTab;

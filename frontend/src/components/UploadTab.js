import React, { useState } from 'react';
import {
  VStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  Alert,
  AlertIcon,
  AlertDescription,
  Box,
  Text,
  Icon,
  Center,
  Spinner,
  Progress,
} from '@chakra-ui/react';
import { FiUpload } from 'react-icons/fi';
import axios from 'axios';

function UploadTab() {
  const [file, setFile] = useState(null);
  const [collection, setCollection] = useState('documents');
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage({ type: 'error', text: 'Please select a file' });
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection', collection);

    try {
      const response = await axios.post('/upload_file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      let messageText = response.data.message;
      if (response.data.success && response.data.file_type === 'image') {
        messageText += ` | Vector dimension: ${response.data.vector_dim}`;
      }

      setMessage({
        type: response.data.success ? 'success' : 'error',
        text: messageText,
      });

      if (response.data.success) {
        setFile(null);
        e.target.reset();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error uploading file' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
<Box
          backdropFilter="blur(8px)"
          background="rgba(100,200,255,0.05)"
          border="1px solid rgba(100,200,255,0.3)"
          borderRadius="20px"
          p={6}
          transition="all 300ms ease-in-out"
          _hover={{
            transform: "translateY(-2px)",
            borderColor: "rgba(100,200,255,0.3)",
          }}
        >
      <VStack spacing={6} align="stretch">
<Box
          backdropFilter="blur(8px)"
          background="rgba(100,200,255,0.05)"
          border="1px solid rgba(100,200,255,0.3)"
          borderRadius="20px"
          p={6}
          transition="all 300ms ease-in-out"
          _hover={{
            transform: "translateY(-2px)",
            borderColor: "rgba(100,200,255,0.3)",
          }}
        >
          <Text fontSize="xl" fontWeight="700" color="white" letterSpacing="wide" mb={2}>
            Upload Document or Image
          </Text>
          <Text color="rgba(255,255,255,0.7)">
            Documents: TXT, PDF, MD, JSON, CSV, LOG
          </Text>
          <Text color="rgba(16,185,129,0.9)" fontWeight="600" mt={1}>
            ✨ Images: PNG, JPG, JPEG, GIF, BMP, WEBP (Vector extraction with CLIP)
          </Text>
        </Box>

        <Alert status="info" borderRadius="12px">
          <AlertIcon />
          <Box>
            <Text fontWeight="600" mb={1}>Image Vectorization</Text>
            <Text fontSize="sm">
              Images are processed using CLIP (Contrastive Language-Image Pre-training) to extract 512-dimensional semantic vectors for similarity search.
            </Text>
          </Box>
        </Alert>

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>Select File</FormLabel>
              <Input
                type="file"
                accept=".txt,.pdf,.md,.json,.csv,.log,.png,.jpg,.jpeg,.gif,.bmp,.webp"
                onChange={(e) => setFile(e.target.files[0])}
                p={1}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Collection Name</FormLabel>
              <Input
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                placeholder="documents"
              />
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={FiUpload} />}
              isLoading={isLoading}
              loadingText="Uploading..."
            >
              Upload & Store in Milvus
            </Button>
          </VStack>
        </form>

        {isLoading && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text color="rgba(255,255,255,0.7)">Loading...</Text>
              <Progress
                w="80%"
                size="sm"
                isIndeterminate
                colorScheme="brand"
                borderRadius="20px"
              />
            </VStack>
          </Center>
        )}

        {message && (
          <Alert status={message.type} borderRadius="20px">
            <AlertIcon />
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}
      </VStack>
    </Box>
  );
}

export default UploadTab;

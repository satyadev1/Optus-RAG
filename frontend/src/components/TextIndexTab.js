import React, { useState } from 'react';
import {
  VStack,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Button,
  Alert,
  AlertIcon,
  AlertDescription,
  Box,
  Text,
  Icon,
  List,
  ListItem,
  ListIcon,
  Tag,
  HStack,
  IconButton,
  Center,
  Spinner,
  Progress,
} from '@chakra-ui/react';
import { FiFileText } from 'react-icons/fi';
import { CheckCircleIcon, CloseIcon } from '@chakra-ui/icons';
import axios from 'axios';

function TextIndexTab() {
  const [title, setTitle] = useState('');

  const descColor = "rgba(255,255,255,0.7)";
  const bgColor = "rgba(255,255,255,0.08)";
  const borderColor = "rgba(255,255,255,0.15)";
  const hoverBg = "rgba(255,255,255,0.12)";
  const [content, setContent] = useState('');
  const [collection, setCollection] = useState('custom_notes');
  const [tags, setTags] = useState('');
  const [tagList, setTagList] = useState([]);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const wordCount = content.trim().split(/\s+/).filter(w => w).length;
  const charCount = content.length;

  const handleAddTag = () => {
    if (tags.trim() && !tagList.includes(tags.trim())) {
      setTagList([...tagList, tags.trim()]);
      setTags('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setTagList(tagList.filter(tag => tag !== tagToRemove));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      setMessage({ type: 'error', text: 'Please enter both title and content' });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const response = await axios.post('/index_text', {
        title: title.trim(),
        content: content.trim(),
        collection: collection,
        tags: tagList,
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: response.data.message
        });
        // Clear form
        setTitle('');
        setContent('');
        setTagList([]);
      } else {
        setMessage({
          type: 'error',
          text: response.data.message
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Error indexing text. Please try again.'
      });
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
          <Text fontSize="xl" fontWeight="bold" mb={2}>
            📝 Index Text - Add Custom Content
          </Text>
          <Text color={descColor}>
            Directly add text content that AI can retrieve and search
          </Text>
        </Box>

        <Alert status="info" borderRadius="20px">
          <AlertIcon />
          <Box flex="1">
            <Text fontWeight="bold" mb={1}>Quick Text Indexing</Text>
            <List spacing={1} fontSize="md">
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Add notes, documentation, or any text content
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Instantly searchable via semantic search
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Retrievable by Claude AI and Ollama AI
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Organize with tags and collections
              </ListItem>
            </List>
          </Box>
        </Alert>

        <form onSubmit={handleSubmit}>
          <VStack
            spacing={6}
            align="stretch"
            backdropFilter="blur(8px)"
            background="rgba(100,200,255,0.08)"
            border="1px solid rgba(255,255,255,0.15)"
            borderRadius="20px"
            p={8}
            boxShadow="0 8px 32px rgba(0,0,0,0.25)"
            transition="all 300ms ease-in-out"
            _hover={{
              boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
            }}
          >
            <FormControl isRequired>
              <FormLabel>Title</FormLabel>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., 'Meeting Notes - Q1 Planning' or 'API Documentation Summary'"
                size="lg"
              />
              <Text fontSize="md" color={descColor} mt={1}>
                Give your content a descriptive title for easy identification
              </Text>
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Content</FormLabel>
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter your text content here... This can be meeting notes, documentation, instructions, code snippets, explanations, or any text you want AI to access."
                rows={12}
                resize="vertical"
              />
              <HStack justify="space-between" mt={1}>
                <Text fontSize="md" color={descColor}>
                  Write or paste any text content you want to make searchable
                </Text>
                <Text fontSize="md" color={descColor}>
                  {wordCount} words | {charCount} characters
                </Text>
              </HStack>
            </FormControl>

            <FormControl>
              <FormLabel>Collection Name</FormLabel>
              <Input
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                placeholder="custom_notes"
              />
              <Text fontSize="md" color={descColor} mt={1}>
                Organize by collection (e.g., meeting_notes, procedures, knowledge_base)
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel>Tags (Optional)</FormLabel>
              <HStack>
                <Input
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                  placeholder="Add tags for categorization (press Enter to add)"
                />
                <Button onClick={handleAddTag} colorScheme="blue" size="md">
                  Add Tag
                </Button>
              </HStack>
              <Text fontSize="md" color={descColor} mt={1}>
                Add keywords or categories (e.g., security, API, frontend, urgent)
              </Text>
              {tagList.length > 0 && (
                <HStack mt={3} spacing={2} flexWrap="wrap">
                  {tagList.map((tag, index) => (
                    <Tag
                      key={index}
                      size="md"
                      borderRadius="full"
                      variant="solid"
                      colorScheme="blue"
                    >
                      {tag}
                      <IconButton
                        size="xs"
                        ml={2}
                        icon={<CloseIcon boxSize={2} />}
                        onClick={() => handleRemoveTag(tag)}
                        variant="ghost"
                        colorScheme="blue"
                        aria-label="Remove tag"
                      />
                    </Tag>
                  ))}
                </HStack>
              )}
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={FiFileText} />}
              isLoading={isLoading}
              loadingText="Indexing..."
              isDisabled={!title.trim() || !content.trim()}
            >
              📥 Index Text Content
            </Button>
            <Text fontSize="md" color="gray.500" textAlign="center">
              Content will be immediately searchable via AI and semantic search
            </Text>
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

        {message?.type === 'success' && (
          <Box p={4} borderWidth={2} borderRadius="20px" borderColor="green.500" bg="green.50">
            <Text fontWeight="bold" color="green.700" mb={2}>
              ✓ Content Successfully Indexed
            </Text>
            <Text fontSize="md" color="green.600">
              Your text has been stored in collection "<strong>{collection}</strong>" and is now searchable.
            </Text>
            <Text fontSize="md" color="green.600" mt={2}>
              <strong>Try it:</strong> Go to Claude AI or Ollama AI tabs and ask questions about your content!
            </Text>
          </Box>
        )}

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
          <Text fontWeight="bold" mb={2}>💡 Example Use Cases</Text>
          <List spacing={2} fontSize="md">
            <ListItem>
              <Text><strong>Meeting Notes:</strong> "Decisions from Q1 planning meeting - migrate to microservices, hire 2 devs"</Text>
            </ListItem>
            <ListItem>
              <Text><strong>Procedures:</strong> "How to deploy to production: 1. Run tests, 2. Create PR, 3. Get approval..."</Text>
            </ListItem>
            <ListItem>
              <Text><strong>API Docs:</strong> "Authentication endpoint /api/auth accepts POST with email/password, returns JWT token"</Text>
            </ListItem>
            <ListItem>
              <Text><strong>Troubleshooting:</strong> "Fix for 502 errors: Restart nginx service, check backend health endpoint"</Text>
            </ListItem>
            <ListItem>
              <Text><strong>Code Snippets:</strong> "Python decorator for rate limiting: @ratelimit(max_calls=10, period=60)"</Text>
            </ListItem>
          </List>
        </Box>
      </VStack>
    </Box>
  );
}

export default TextIndexTab;

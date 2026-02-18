import React, { useState } from 'react';
import {
  VStack,
  HStack,
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
  Spinner,
  Center,
  Progress,
  List,
  ListItem,
  ListIcon,
  Badge,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';
import { SiConfluence } from 'react-icons/si';
import { CheckCircleIcon } from '@chakra-ui/icons';
import axios from 'axios';

function ConfluenceTab() {
  const [pageUrl, setPageUrl] = useState('');
  const [collection, setCollection] = useState('confluence_pages');
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [pageInfo, setPageInfo] = useState(null);

  const descColor = 'rgba(255,255,255,0.7)';
  const bgColor = 'rgba(255,255,255,0.08)';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pageUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a Confluence page URL' });
      return;
    }

    setIsLoading(true);
    setMessage(null);
    setPageInfo(null);

    try {
      const response = await axios.post('/fetch_confluence', {
        page_url: pageUrl,
        collection: collection,
      });

      setMessage({
        type: response.data.success ? 'success' : 'error',
        text: response.data.message,
      });

      if (response.data.success) {
        setPageInfo(response.data.page_info);
        setPageUrl('');
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.message || 'Error fetching Confluence page'
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
            📚 Import Confluence Pages
          </Text>
          <Text color={descColor}>
            Fetch wiki pages from Confluence using Jira credentials
          </Text>
        </Box>

        <Alert status="info" borderRadius="20px">
          <AlertIcon />
          <Box flex="1">
            <Text fontWeight="bold" mb={1}>What Gets Fetched</Text>
            <List spacing={1} fontSize="md">
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Page title, content (converted from HTML to text)
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Space information and breadcrumb navigation
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Version history, creator, and last modified details
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Parent pages (ancestors) for context
              </ListItem>
            </List>
          </Box>
        </Alert>

        <Alert status="warning" borderRadius="20px">
          <AlertIcon />
          <Box flex="1">
            <Text fontWeight="bold" mb={1}>Authentication</Text>
            <Text fontSize="md">
              Uses Jira credentials from .env file (JIRA_EMAIL and JIRA_API_TOKEN).
              Make sure you have access to the Confluence space.
            </Text>
          </Box>
        </Alert>

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>Confluence Page URL</FormLabel>
              <Input
                value={pageUrl}
                onChange={(e) => setPageUrl(e.target.value)}
                placeholder="https://your-instance.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title"
                type="url"
              />
              <Text fontSize="md" color={descColor} mt={1}>
                Example: https://your-instance.atlassian.net/wiki/spaces/TEAM/pages/123456/Documentation+Page
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel>Collection Name</FormLabel>
              <Input
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                placeholder="confluence_pages"
              />
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={SiConfluence} />}
              isLoading={isLoading}
              loadingText="Fetching page..."
            >
              📥 Fetch Confluence Page
            </Button>
          </VStack>
        </form>

        {isLoading && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text color="rgba(255,255,255,0.7)">Fetching Confluence page content...</Text>
              <Progress
                w="80%"
                size="sm"
                isIndeterminate
                colorScheme="brand"
                borderRadius="20px"
              />
              <Text fontSize="md" color="gray.500">
                Converting HTML to text and extracting metadata...
              </Text>
            </VStack>
          </Center>
        )}

        {message && (
          <Alert status={message.type} borderRadius="20px">
            <AlertIcon />
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        {pageInfo && (
          <>
            <Divider />
            <Box p={6} bg={bgColor} borderRadius="20px">
              <Text fontSize="lg" fontWeight="bold" mb={4}>
                📄 Page Details
              </Text>
              <VStack spacing={3} align="stretch">
                <HStack>
                  <Text fontWeight="bold" minW="150px">Title:</Text>
                  <Text>{pageInfo.title}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="bold" minW="150px">Page ID:</Text>
                  <Badge colorScheme="blue">{pageInfo.page_id}</Badge>
                </HStack>
                <HStack>
                  <Text fontWeight="bold" minW="150px">Space:</Text>
                  <Badge colorScheme="blue">{pageInfo.space}</Badge>
                </HStack>
                <HStack>
                  <Text fontWeight="bold" minW="150px">Version:</Text>
                  <Text>{pageInfo.version}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="bold" minW="150px">Created by:</Text>
                  <Text>{pageInfo.created_by}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="bold" minW="150px">Last modified by:</Text>
                  <Text>{pageInfo.last_modified_by}</Text>
                </HStack>
              </VStack>
            </Box>

            <Alert status="success" borderRadius="20px">
              <AlertIcon />
              <Box flex="1">
                <Text fontWeight="bold" mb={1}>Next Steps</Text>
                <Text fontSize="md">
                  Go to "Claude AI" or "Ollama AI" tabs to query this page content.
                  Select the "{collection}" collection to include Confluence data in your queries.
                </Text>
              </Box>
            </Alert>
          </>
        )}
      </VStack>
    </Box>
  );
}

export default ConfluenceTab;

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
  Spinner,
  Center,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { AiOutlineGithub } from 'react-icons/ai';
import { CheckCircleIcon } from '@chakra-ui/icons';
import axios from 'axios';

function GitHubTab() {
  const [prUrl, setPrUrl] = useState('');
  const [collection, setCollection] = useState('github_prs');
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');

  const descColor = 'rgba(255,255,255,0.7)';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a GitHub PR URL' });
      return;
    }

    setIsLoading(true);
    setMessage(null);
    setLoadingStatus('Fetching PR details...');

    try {
      const response = await axios.post('/fetch_github_pr', {
        pr_url: prUrl,
        collection: collection,
      });

      setMessage({
        type: response.data.success ? 'success' : 'error',
        text: response.data.message,
      });

      if (response.data.success) {
        setPrUrl('');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error fetching GitHub PR' });
    } finally {
      setIsLoading(false);
      setLoadingStatus('');
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
            🐙 Import GitHub Pull Request (Full Analysis)
          </Text>
          <Text color={descColor}>
            Enter a GitHub PR URL to fetch and analyze all available data
          </Text>
        </Box>

        <Alert status="info" borderRadius="20px">
          <AlertIcon />
          <Box flex="1">
            <Text fontWeight="bold" mb={1}>Enhanced PR Analysis</Text>
            <List spacing={1} fontSize="md">
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                All commits, file changes, and diffs
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Reviews (approvals, changes requested, comments)
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Discussion comments and inline code review comments
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Timeline events, labels, and assignees
              </ListItem>
            </List>
          </Box>
        </Alert>

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>GitHub PR URL</FormLabel>
              <Input
                value={prUrl}
                onChange={(e) => setPrUrl(e.target.value)}
                placeholder="https://github.com/owner/repo/pull/123"
                type="url"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Collection Name</FormLabel>
              <Input
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                placeholder="github_prs"
              />
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={AiOutlineGithub} />}
              isLoading={isLoading}
              loadingText="Analyzing PR..."
            >
              🔍 Fetch & Analyze PR
            </Button>
          </VStack>
        </form>

        {isLoading && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text color="rgba(255,255,255,0.7)">{loadingStatus}</Text>
              <Text fontSize="md" color="gray.500">
                Fetching commits, reviews, comments, and file changes...
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
      </VStack>
    </Box>
  );
}

export default GitHubTab;

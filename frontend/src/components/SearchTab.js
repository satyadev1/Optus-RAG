import React, { useState } from 'react';
import {
  VStack,
  FormControl,
  FormLabel,
  Textarea,
  Input,
  Button,
  Alert,
  AlertIcon,
  AlertDescription,
  Box,
  Text,
  Icon,
  Heading,
  Badge,
  Link,
  Spinner,
  Center,
  Progress,
} from '@chakra-ui/react';
import { FiSearch } from 'react-icons/fi';
import axios from 'axios';
import AnimatedSelect from './AnimatedSelect';

function SearchTab() {
  const [query, setQuery] = useState('');
  const [collection, setCollection] = useState('jira_tickets');
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setMessage({ type: 'error', text: 'Please enter a search query' });
      return;
    }

    setIsLoading(true);
    setResults([]);
    setMessage(null);

    try {
      const response = await axios.post('/search', {
        query: query,
        collection: collection,
        top_k: topK,
      });

      if (response.data.success) {
        setResults(response.data.results);
        if (response.data.results.length === 0) {
          setMessage({ type: 'info', text: 'No results found' });
        }
      } else {
        setMessage({ type: 'error', text: response.data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error performing search' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box animation="fadeInUp 350ms ease-in-out">
      <VStack spacing={8} align="stretch">
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
          <Text fontSize="xl" fontWeight="bold" mb={3}>
            Semantic Vector Search
          </Text>
          <Text color="rgba(255,255,255,0.7)">
            Search across your data using AI-powered semantic understanding
          </Text>
        </Box>

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
              <FormLabel>Search Query</FormLabel>
              <Textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., 'firewall docker quarantine issues' or 'feature flags'"
                rows={3}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Collection</FormLabel>
              <AnimatedSelect
                value={collection}
                onChange={setCollection}
                placeholder="Select Collection"
                options={[
                  { value: 'jira_tickets', label: '📋 Jira Tickets' },
                  { value: 'github_prs', label: '🔀 GitHub PRs' },
                  { value: 'documents', label: '📄 Documents' },
                ]}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Number of Results</FormLabel>
              <Input
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                min={1}
                max={20}
              />
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={FiSearch} />}
              isLoading={isLoading}
              loadingText="Searching..."
            >
              🔍 Search with AI
            </Button>
          </VStack>
        </form>

        {message && (
          <Alert status={message.type} borderRadius="20px">
            <AlertIcon />
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        {isLoading && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text color="rgba(255,255,255,0.7)">Searching...</Text>
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

        {results.length > 0 && (
          <VStack spacing={4} align="stretch" mt={4}>
            {results.map((result, index) => (
              <Box
                key={index}
                p={5}
                borderWidth={1}
                borderRadius="20px"
                borderColor="gray.200"
                _hover={{
                  borderColor: 'brand.500',
                  shadow: 'md',
                  transform: 'translateX(4px)',
                }}
                transition="all 0.2s"
              >
                <Heading size="md" mb={2} color="brand.600">
                  {index + 1}. {result.title}
                  <Badge ml={3} colorScheme="blue" fontSize="md">
                    Score: {result.similarity_score}
                  </Badge>
                </Heading>
                <Text color="gray.700" mb={3}>
                  {result.content}
                </Text>
                <Box fontSize="md" color="gray.500">
                  <Text>
                    <strong>Type:</strong> {result.source_type} |{' '}
                    <strong>ID:</strong> {result.source_id}
                  </Text>
                  <Link href={result.url} isExternal color="brand.500">
                    {result.url}
                  </Link>
                </Box>
              </Box>
            ))}
          </VStack>
        )}
      </VStack>
    </Box>
  );
}

export default SearchTab;

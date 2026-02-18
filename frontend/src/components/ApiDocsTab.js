import React from 'react';
import {
  Box,
  VStack,
  Heading,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Code,
  Divider,
  Badge,
  useColorMode,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  HStack,
} from '@chakra-ui/react';

function ApiDocsTab() {
  const { colorMode } = useColorMode();

  const endpoints = [
    {
      method: 'POST',
      path: '/ask_claude',
      description: 'Query Claude AI with RAG context',
      params: [
        { name: 'question', type: 'string', required: true, description: 'The question to ask' },
        { name: 'collection', type: 'string', required: false, description: 'Collection to search (all, jira_tickets, github_prs, documents)' },
        { name: 'website_url', type: 'string', required: false, description: 'Optional website URL to scrape and include' },
        { name: 'top_k', type: 'number', required: false, description: 'Number of documents to retrieve (default: 3)' },
        { name: 'context', type: 'array', required: false, description: 'Previous conversation context' },
      ],
      response: {
        success: 'boolean',
        answer: 'string',
        model: 'string',
        sources: 'array',
        website_scraped: 'string',
      },
    },
    {
      method: 'POST',
      path: '/ask_ollama',
      description: 'Query Ollama AI with RAG context',
      params: [
        { name: 'question', type: 'string', required: true, description: 'The question to ask' },
        { name: 'collection', type: 'string', required: false, description: 'Collection to search' },
        { name: 'model', type: 'string', required: false, description: 'Ollama model to use (default: deepseek-r1:8b)' },
        { name: 'top_k', type: 'number', required: false, description: 'Number of documents to retrieve' },
        { name: 'context', type: 'array', required: false, description: 'Previous conversation context' },
      ],
      response: {
        success: 'boolean',
        answer: 'string',
        model: 'string',
        sources: 'array',
      },
    },
    {
      method: 'POST',
      path: '/search',
      description: 'Semantic search across collections',
      params: [
        { name: 'query', type: 'string', required: true, description: 'Search query' },
        { name: 'collection', type: 'string', required: true, description: 'Collection name' },
        { name: 'top_k', type: 'number', required: false, description: 'Number of results (default: 5)' },
      ],
      response: {
        success: 'boolean',
        results: 'array',
      },
    },
    {
      method: 'POST',
      path: '/index_text',
      description: 'Index custom text into Milvus',
      params: [
        { name: 'title', type: 'string', required: true, description: 'Document title' },
        { name: 'content', type: 'string', required: true, description: 'Document content' },
        { name: 'source_type', type: 'string', required: true, description: 'Type of source' },
        { name: 'collection', type: 'string', required: true, description: 'Target collection' },
      ],
      response: {
        success: 'boolean',
        message: 'string',
      },
    },
    {
      method: 'POST',
      path: '/upload',
      description: 'Upload and index files (PDF, TXT, DOCX, MD)',
      params: [
        { name: 'file', type: 'file', required: true, description: 'File to upload' },
        { name: 'collection', type: 'string', required: false, description: 'Target collection (default: documents)' },
      ],
      response: {
        success: 'boolean',
        message: 'string',
        chunks: 'number',
      },
    },
    {
      method: 'POST',
      path: '/fetch_jira',
      description: 'Fetch and index Jira tickets',
      params: [
        { name: 'jql', type: 'string', required: false, description: 'JQL query (default: project=PROJ)' },
        { name: 'max_results', type: 'number', required: false, description: 'Maximum tickets to fetch' },
      ],
      response: {
        success: 'boolean',
        message: 'string',
        count: 'number',
      },
    },
    {
      method: 'POST',
      path: '/fetch_github',
      description: 'Fetch and index GitHub PRs',
      params: [
        { name: 'repo', type: 'string', required: true, description: 'Repository (owner/repo)' },
        { name: 'state', type: 'string', required: false, description: 'PR state (all, open, closed)' },
        { name: 'max_results', type: 'number', required: false, description: 'Maximum PRs to fetch' },
      ],
      response: {
        success: 'boolean',
        message: 'string',
        count: 'number',
      },
    },
    {
      method: 'POST',
      path: '/crawl_website',
      description: 'Crawl and index website content',
      params: [
        { name: 'url', type: 'string', required: true, description: 'Starting URL' },
        { name: 'max_pages', type: 'number', required: false, description: 'Maximum pages to crawl (default: 10)' },
      ],
      response: {
        success: 'boolean',
        message: 'string',
        pages_crawled: 'number',
      },
    },
    {
      method: 'GET',
      path: '/ollama_status',
      description: 'Check Ollama server status',
      params: [],
      response: {
        running: 'boolean',
        models: 'array',
      },
    },
  ];

  return (
    <Box animation="fadeInUp 350ms ease-in-out">
      <VStack spacing={8} align="stretch">
        <Box
          backdropFilter="blur(8px)"
          background={colorMode === 'dark' ? 'rgba(100,200,255,0.05)' : 'rgba(255,255,255,0.7)'}
          border="1px solid"
          borderColor={colorMode === 'dark' ? 'rgba(100,200,255,0.3)' : 'rgba(100,116,139,0.2)'}
          borderRadius="20px"
          p={6}
          transition="all 300ms ease-in-out"
        >
          <Heading size="lg" mb={3} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
            API Documentation
          </Heading>
          <Text color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>
            Complete REST API documentation for RAG system platform
          </Text>
        </Box>

        <Tabs colorScheme="blue" variant="soft-rounded">
          <TabList>
            <Tab>Endpoints</Tab>
            <Tab>Swagger UI</Tab>
            <Tab>Examples</Tab>
          </TabList>

          <TabPanels>
            {/* Endpoints Tab */}
            <TabPanel>
              <VStack spacing={6} align="stretch">
                {endpoints.map((endpoint, idx) => (
                  <Box
                    key={idx}
                    p={6}
                    backdropFilter="blur(8px)"
                    background={colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)'}
                    border="1px solid"
                    borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)'}
                    borderRadius="16px"
                    transition="all 300ms ease-in-out"
                    _hover={{
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
                    }}
                  >
                    <HStack mb={3}>
                      <Badge
                        colorScheme={endpoint.method === 'GET' ? 'green' : 'blue'}
                        fontSize="sm"
                        px={3}
                        py={1}
                        borderRadius="8px"
                      >
                        {endpoint.method}
                      </Badge>
                      <Code
                        px={3}
                        py={1}
                        borderRadius="8px"
                        bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                        color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}
                      >
                        {endpoint.path}
                      </Code>
                    </HStack>

                    <Text mb={4} color={colorMode === 'dark' ? 'rgba(255,255,255,0.8)' : 'rgba(30,41,59,0.8)'}>
                      {endpoint.description}
                    </Text>

                    {endpoint.params.length > 0 && (
                      <>
                        <Heading size="sm" mb={3} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
                          Parameters
                        </Heading>
                        <Table size="sm" variant="simple" mb={4}>
                          <Thead>
                            <Tr>
                              <Th color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>Name</Th>
                              <Th color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>Type</Th>
                              <Th color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>Required</Th>
                              <Th color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>Description</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {endpoint.params.map((param, pidx) => (
                              <Tr key={pidx}>
                                <Td>
                                  <Code fontSize="xs" color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}>
                                    {param.name}
                                  </Code>
                                </Td>
                                <Td color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>
                                  {param.type}
                                </Td>
                                <Td>
                                  <Badge colorScheme={param.required ? 'red' : 'gray'}>
                                    {param.required ? 'Yes' : 'No'}
                                  </Badge>
                                </Td>
                                <Td color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>
                                  {param.description}
                                </Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      </>
                    )}

                    <Heading size="sm" mb={3} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
                      Response
                    </Heading>
                    <Code
                      display="block"
                      whiteSpace="pre"
                      p={4}
                      borderRadius="12px"
                      bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                      color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}
                    >
                      {JSON.stringify(endpoint.response, null, 2)}
                    </Code>
                  </Box>
                ))}
              </VStack>
            </TabPanel>

            {/* Swagger UI Tab */}
            <TabPanel>
              <Box
                p={6}
                backdropFilter="blur(8px)"
                background={colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)'}
                border="1px solid"
                borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)'}
                borderRadius="16px"
              >
                <Heading size="md" mb={4} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
                  Interactive API Explorer
                </Heading>
                <Text mb={4} color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>
                  Access the full Swagger UI interface at:
                </Text>
                <Code
                  display="block"
                  p={4}
                  borderRadius="12px"
                  bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                  color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}
                  fontSize="lg"
                >
                  http://localhost:5001/api/docs
                </Code>
                <Divider my={6} />
                <Text mb={4} color={colorMode === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(30,41,59,0.7)'}>
                  Open in new tab for full interactive documentation
                </Text>
                <Box
                  as="iframe"
                  src="http://localhost:5001/api/docs"
                  width="100%"
                  height="700px"
                  borderRadius="12px"
                  border="1px solid"
                  borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)'}
                  bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'white'}
                />
              </Box>
            </TabPanel>

            {/* Examples Tab */}
            <TabPanel>
              <VStack spacing={6} align="stretch">
                <Box
                  p={6}
                  backdropFilter="blur(8px)"
                  background={colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)'}
                  border="1px solid"
                  borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)'}
                  borderRadius="16px"
                >
                  <Heading size="md" mb={4} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
                    Example: Query Claude AI
                  </Heading>
                  <Code
                    display="block"
                    whiteSpace="pre"
                    p={4}
                    borderRadius="12px"
                    bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                    color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}
                    overflowX="auto"
                  >
{`curl -X POST http://localhost:5001/ask_claude \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "What are the main issues in development?",
    "collection": "all",
    "top_k": 3
  }'`}
                  </Code>
                </Box>

                <Box
                  p={6}
                  backdropFilter="blur(8px)"
                  background={colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)'}
                  border="1px solid"
                  borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)'}
                  borderRadius="16px"
                >
                  <Heading size="md" mb={4} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
                    Example: Semantic Search
                  </Heading>
                  <Code
                    display="block"
                    whiteSpace="pre"
                    p={4}
                    borderRadius="12px"
                    bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                    color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}
                    overflowX="auto"
                  >
{`curl -X POST http://localhost:5001/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "docker firewall issues",
    "collection": "jira_tickets",
    "top_k": 5
  }'`}
                  </Code>
                </Box>

                <Box
                  p={6}
                  backdropFilter="blur(8px)"
                  background={colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)'}
                  border="1px solid"
                  borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)'}
                  borderRadius="16px"
                >
                  <Heading size="md" mb={4} color={colorMode === 'dark' ? 'rgba(165,180,252,1)' : '#4338ca'}>
                    Example: JavaScript/Axios
                  </Heading>
                  <Code
                    display="block"
                    whiteSpace="pre"
                    p={4}
                    borderRadius="12px"
                    bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                    color={colorMode === 'dark' ? '#a5b4fc' : '#4338ca'}
                    overflowX="auto"
                  >
{`import axios from 'axios';

const response = await axios.post('/ask_claude', {
  question: 'Summarize all feature flag work',
  collection: 'all',
  top_k: 5
});

console.log(response.data.answer);
console.log(response.data.sources);`}
                  </Code>
                </Box>
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
}

export default ApiDocsTab;

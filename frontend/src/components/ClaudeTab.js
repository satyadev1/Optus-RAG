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
  Divider,
  Progress,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import { GiBrain } from 'react-icons/gi';
import axios from 'axios';
import AnimatedSelect from './AnimatedSelect';

function ClaudeTab() {
  const answerBg = 'rgba(77,124,178,0.1)';
  const answerBoxBg = 'rgba(255,255,255,0.08)';
  const sourceBg = 'rgba(255,255,255,0.08)';
  const websiteBg = 'rgba(16,185,129,0.1)';
  const [question, setQuestion] = useState('');
  const [collection, setCollection] = useState('all');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [topK, setTopK] = useState(3);
  const [answer, setAnswer] = useState(null);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      setMessage({ type: 'error', text: 'Please enter a question' });
      return;
    }

    setIsLoading(true);
    setAnswer(null);
    setMessage(null);

    try {
      const response = await axios.post('/ask_claude', {
        question: question,
        collection: collection,
        website_url: websiteUrl,
        top_k: topK,
      });

      if (response.data.success) {
        setAnswer(response.data);
      } else {
        setMessage({ type: 'error', text: response.data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error connecting to Claude API' });
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
          <VStack align="start" spacing={3}>
            <Text
              fontSize="3xl"
              fontWeight="700"
              color="white"
              letterSpacing="wide"
            >
              🧠 CLAUDE AI
            </Text>
            <Text fontSize="md" fontWeight="600" color="rgba(199,210,254,1)" letterSpacing="wide">
              Advanced RAG with Multi-Source Context
            </Text>
            <Text color="rgba(255,255,255,0.6)" fontSize="md" lineHeight="tall">
              Ask questions across ALL your data (Jira + GitHub + Documents + Websites) with Claude's advanced reasoning
            </Text>
          </VStack>
        </Box>

        <Alert
          status="info"
          borderRadius="20px"
          backdropFilter="blur(8px)"
          background="rgba(77,124,178,0.08)"
          border="1px solid rgba(77,124,178,0.25)"
          boxShadow="0 8px 32px rgba(77,124,178,0.2)"
          transition="all 300ms ease-in-out"
          _hover={{
            background: "rgba(77,124,178,0.12)",
            borderColor: "rgba(77,124,178,0.35)",
          }}
        >
          <AlertIcon color="rgba(165,180,252,1)" />
          <Box flex="1">
            <Text fontWeight="700" mb={3} fontSize="md" color="rgba(199,210,254,1)" letterSpacing="wide">
              Hybrid AI - Best of Both Worlds
            </Text>
            <VStack align="start" spacing={2}>
              <Text fontSize="md" color="rgba(255,255,255,0.8)">
                • Claude uses BOTH retrieved documents AND its own knowledge
              </Text>
              <Text fontSize="md" color="rgba(255,255,255,0.8)">
                • Prioritizes your data, supplements with general knowledge
              </Text>
              <Text fontSize="md" color="rgba(199,210,254,1)" fontWeight="600">
                ⚡ Tip: Use 3 docs/source for 2-3x faster responses
              </Text>
            </VStack>
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
              <FormLabel>Your Question</FormLabel>
              <Textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g., 'What Docker firewall issues are in development?' or 'Summarize all work related to feature flags'"
                rows={4}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Data Sources</FormLabel>
              <AnimatedSelect
                value={collection}
                onChange={setCollection}
                placeholder="Select Data Source"
                options={[
                  { value: 'all', label: '🌟 All Collections' },
                  { value: 'jira_tickets', label: '📋 Jira Tickets' },
                  { value: 'github_prs', label: '🔀 GitHub PRs' },
                  { value: 'documents', label: '📄 Documents' },
                ]}
              />
              <Text fontSize="md" color="gray.500" mt={1}>
                Recommended: Use "All Collections" for comprehensive answers
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel>Website URL (Optional)</FormLabel>
              <Input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com/docs"
              />
              <Text fontSize="md" color="gray.500" mt={1}>
                Add any website to scrape and include in the context (documentation, articles, etc.)
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel>Documents per Source</FormLabel>
              <Input
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                min={1}
                max={10}
              />
              <Text fontSize="md" color="gray.500" mt={1}>
                Default: 3 (fast) | Use 5-7 for more context | Lower = faster queries
              </Text>
              <Text fontSize="md" color="blue.500" mt={1}>
                ⚡ Performance Tip: Lower values (1-3) give 2-3x faster responses
              </Text>
            </FormControl>

            <Button
              type="submit"
              colorScheme="blue"
              size="lg"
              leftIcon={<Icon as={GiBrain} />}
              isLoading={isLoading}
              loadingText="Claude is analyzing..."
            >
              🧠 Ask Claude (Advanced AI)
            </Button>
          </VStack>
        </form>

        {message && (
          <Alert status={message.type} borderRadius="md">
            <AlertIcon />
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        {isLoading && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="blue.600" thickness="4px" />
              <Text color="gray.600">Claude is thinking...</Text>
              <Progress
                w="80%"
                size="sm"
                isIndeterminate
                colorScheme="blue"
                borderRadius="md"
              />
              {websiteUrl && (
                <Text fontSize="md" color="gray.500">
                  Scraping website: {websiteUrl}
                </Text>
              )}
            </VStack>
          </Center>
        )}

        {answer && (
          <VStack spacing={6} align="stretch" mt={4}>
            {/* AI Answer */}
            <Box
              p={8}
              backdropFilter="blur(8px)"
              background={answerBg}
              border="2px solid"
              borderColor="rgba(77,124,178,0.5)"
              borderRadius="20px"
              boxShadow="0 8px 32px rgba(77,124,178,0.2)"
              transition="all 300ms ease-in-out"
              animation="fadeInUp 350ms ease-in-out"
              _hover={{
                transform: "translateY(-2px)",
                boxShadow: "0 8px 24px rgba(77,124,178,0.3)",
              }}
            >
              <Heading size="md" mb={4} color="rgba(165,180,252,1)">
                🧠 Claude AI Answer ({answer.model})
              </Heading>
              {answer.website_scraped && (
                <Badge colorScheme="green" mb={3} fontSize="md">
                  ✓ Website scraped: {answer.website_scraped}
                </Badge>
              )}
              <Box
                p={6}
                backdropFilter="blur(8px)"
                background={answerBoxBg}
                border="1px solid rgba(100,200,255,0.3)"
                borderRadius="16px"
                whiteSpace="pre-wrap"
                lineHeight="tall"
              >
                {answer.answer}
              </Box>
            </Box>

            <Divider />

            {/* Source Documents - Compact Accordion */}
            <Accordion allowToggle>
              <AccordionItem
                border="1px solid rgba(255,255,255,0.15)"
                borderRadius="20px"
                overflow="hidden"
              >
                <AccordionButton
                  p={4}
                  backdropFilter="blur(8px)"
                  background="rgba(77,124,178,0.08)"
                  _hover={{ background: 'rgba(77,124,178,0.15)' }}
                  transition="all 200ms"
                >
                  <Box flex="1" textAlign="left">
                    <Heading size="md">
                      📚 Source Documents ({answer.sources.length})
                    </Heading>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel pb={4} pt={4}>
                  <VStack spacing={3} align="stretch">
                    {answer.sources.map((source, index) => (
                      <Box
                        key={index}
                        p={4}
                        backdropFilter="blur(8px)"
                        background={source.source_type === 'website' ? websiteBg : sourceBg}
                        border="1px solid"
                        borderColor={source.source_type === 'website' ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.15)'}
                        borderRadius="12px"
                        _hover={{
                          borderColor: 'rgba(77,124,178,0.5)',
                        }}
                        transition="all 200ms ease-in-out"
                      >
                        <Heading size="xs" mb={2} color="blue.500">
                          {index + 1}. {source.title}
                          <Badge ml={2} colorScheme="blue" fontSize="xs">
                            {source.source_type === 'website' ? '🌐 Website' : `📁 ${source.collection}`}
                          </Badge>
                          <Badge ml={1} colorScheme="green" fontSize="xs">
                            {source.score}
                          </Badge>
                        </Heading>
                        <Text color="gray.700" fontSize="sm" mb={2} noOfLines={2}>
                          {source.content.substring(0, 150)}...
                        </Text>
                        <Link href={source.url} isExternal color="blue.600" fontSize="xs">
                          {source.url}
                        </Link>
                      </Box>
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          </VStack>
        )}
      </VStack>
    </Box>
  );
}

export default ClaudeTab;

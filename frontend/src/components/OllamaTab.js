import React, { useState, useEffect } from 'react';
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
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import { AiOutlineRobot } from 'react-icons/ai';
import axios from 'axios';
import AnimatedSelect from './AnimatedSelect';

function OllamaTab() {
  const [question, setQuestion] = useState('');
  const [collection, setCollection] = useState('jira_tickets');
  const [model, setModel] = useState('deepseek-r1:8b');
  const [topK, setTopK] = useState(3);
  const [answer, setAnswer] = useState(null);
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const answerBg = 'rgba(77,124,178,0.1)';
  const answerBoxBg = 'rgba(255,255,255,0.08)';
  const sourceBg = 'rgba(255,255,255,0.08)';

  useEffect(() => {
    checkOllamaStatus();
  }, []);

  const checkOllamaStatus = async () => {
    try {
      const response = await axios.get('/ollama_status');
      setOllamaStatus(response.data);
    } catch (error) {
      setOllamaStatus({ running: false, models: [] });
    }
  };

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
      const response = await axios.post('/ask_ollama', {
        question: question,
        collection: collection,
        model: model,
        top_k: topK,
      });

      if (response.data.success) {
        setAnswer(response.data);
      } else {
        setMessage({ type: 'error', text: response.data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error connecting to Ollama' });
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
            🤖 Ollama AI - Offline Reasoning (RAG)
          </Text>
          <Text color="rgba(255,255,255,0.7)">
            Ask questions and get intelligent answers powered by Ollama AI with context from your Milvus database
          </Text>
        </Box>

        {ollamaStatus && (
          <Alert
            status={ollamaStatus.running ? 'success' : 'warning'}
            borderRadius="20px"
          >
            <AlertIcon />
            <Box flex="1">
              {ollamaStatus.running ? (
                <Text>
                  ✓ Ollama is running | Available models:{' '}
                  {ollamaStatus.models.join(', ') || 'None'}
                </Text>
              ) : (
                <Text>
                  ✗ Ollama not running. Start it with: <code>ollama serve</code>
                </Text>
              )}
            </Box>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>Your Question</FormLabel>
              <Textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask anything... e.g., 'What Docker firewall issues are currently in development?' or 'Summarize all feature flag related work'"
                rows={4}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Search Collection</FormLabel>
              <AnimatedSelect
                value={collection}
                onChange={setCollection}
                placeholder="Select Collection"
                options={[
                  { value: 'all', label: '🌟 All Collections' },
                  { value: 'jira_tickets', label: '📋 Jira Tickets' },
                  { value: 'github_prs', label: '🔀 GitHub PRs' },
                  { value: 'documents', label: '📄 Documents' },
                ]}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Website URL (Optional)</FormLabel>
              <Input
                type="url"
                placeholder="https://example.com/docs (Leave empty to search only Milvus)"
                onChange={(e) => setQuestion(question + ' [Website: ' + e.target.value + ']')}
              />
              <Text fontSize="md" color="gray.500" mt={1}>
                Add any website to scrape and include in context
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel>Ollama Model</FormLabel>
              <AnimatedSelect
                value={model}
                onChange={setModel}
                placeholder="Select Model"
                options={[
                  { value: 'llama3.2', label: '🦙 Llama 3.2' },
                  { value: 'deepseek-r1:8b', label: '🧠 DeepSeek R1' },
                  { value: 'qwen2.5', label: '🤖 Qwen 2.5' },
                  { value: 'mistral', label: '⚡ Mistral' },
                  { value: 'phi4-reasoning:14b', label: '🔮 Phi4 Reasoning' },
                ]}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Context Documents</FormLabel>
              <Input
                type="number"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                min={1}
                max={10}
              />
              <Text fontSize="md" color="gray.500" mt={1}>
                Default: 3 (fast) | Use 5-7 for more context | Lower = faster
              </Text>
              <Text fontSize="md" color="blue.500" mt={1}>
                ⚡ Tip: Lower values give 2-3x faster responses
              </Text>
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={AiOutlineRobot} />}
              isLoading={isLoading}
              loadingText="AI is thinking..."
            >
              🧠 Ask Ollama AI
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
              <Text color="rgba(255,255,255,0.7)">Ollama AI is thinking...</Text>
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

        {answer && (
          <VStack spacing={6} align="stretch" mt={4}>
            {/* AI Answer */}
            <Box
              p={6}
              bg={answerBg}
              borderWidth={2}
              borderColor="brand.500"
              borderRadius="20px"
            >
              <Heading size="md" mb={4} color="brand.400">
                🤖 Ollama AI Answer ({answer.model})
              </Heading>
              <Box
                p={4}
                bg={answerBoxBg}
                borderRadius="20px"
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
                border="1px solid rgba(100,200,255,0.3)"
                borderRadius="20px"
                overflow="hidden"
              >
                <AccordionButton
                  p={4}
                  backdropFilter="blur(8px)"
                  background="rgba(100,200,255,0.05)"
                  _hover={{ background: 'rgba(100,200,255,0.12)' }}
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
                        bg={sourceBg}
                        border="1px solid rgba(255,255,255,0.15)"
                        borderRadius="12px"
                        _hover={{
                          borderColor: 'brand.500',
                        }}
                        transition="all 200ms"
                      >
                        <Heading size="xs" mb={2} color="brand.400">
                          {index + 1}. {source.title}
                          <Badge ml={2} colorScheme="blue" fontSize="xs">
                            {source.score}
                          </Badge>
                        </Heading>
                        <Text color="gray.700" fontSize="sm" mb={2} noOfLines={2}>
                          {source.content.substring(0, 150)}...
                        </Text>
                        <Link href={source.url} isExternal color="brand.500" fontSize="xs">
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

export default OllamaTab;

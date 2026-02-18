import React, { useState, useEffect, useRef } from 'react';
import {
  VStack,
  HStack,
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
  Center,
  Spinner,
  Progress,
  useColorMode,
  CircularProgress,
  CircularProgressLabel,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react';
import { MdBugReport, MdCheckCircle, MdError } from 'react-icons/md';
import axios from 'axios';

function JiraTab() {
  const { colorMode } = useColorMode();
  const [jiraInput, setJiraInput] = useState('');
  const [collection, setCollection] = useState('jira_tickets');
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [progressFile, setProgressFile] = useState(null);
  const progressIntervalRef = useRef(null);

  // Poll for progress updates
  useEffect(() => {
    if (isLoading && progressFile) {
      progressIntervalRef.current = setInterval(() => {
        fetchProgress();
      }, 2000);

      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    }
  }, [isLoading, progressFile]);

  const fetchProgress = async () => {
    try {
      const response = await axios.get('/jira_progress', {
        params: { progress_file: progressFile },
      });

      setProgress(response.data);

      // Check if completed
      if (response.data.status === 'completed') {
        clearInterval(progressIntervalRef.current);
        setIsLoading(false);
        setMessage({
          type: 'success',
          text: response.data.current_item || 'Successfully fetched Jira tickets',
        });
        setProgressFile(null);
        setProgress(null);
        setJiraInput('');
      } else if (response.data.status === 'error') {
        clearInterval(progressIntervalRef.current);
        setIsLoading(false);
        setMessage({
          type: 'error',
          text: response.data.error_message || 'Error fetching Jira tickets',
        });
        setProgressFile(null);
        setProgress(null);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jiraInput.trim()) {
      setMessage({ type: 'error', text: 'Please enter Jira ticket keys' });
      return;
    }

    setIsLoading(true);
    setProgress(null);
    setMessage(null);

    try {
      const response = await axios.post('/fetch_jira', {
        jira_input: jiraInput,
        collection: collection,
      });

      if (response.data.success && response.data.progress_file) {
        setProgressFile(response.data.progress_file);
        setMessage({
          type: 'info',
          text: response.data.message || 'Fetching Jira tickets...',
        });
      } else {
        setMessage({
          type: 'error',
          text: response.data.message || 'Failed to start fetching',
        });
        setIsLoading(false);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error fetching Jira tickets' });
      setIsLoading(false);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || seconds < 0) return '0s';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const renderProgressBar = () => {
    if (!progress) return null;

    const percent = progress.progress_percent || 0;
    const processed = progress.items_processed || 0;
    const total = progress.total_items || 0;
    const successful = progress.items_successful || 0;
    const failed = progress.items_failed || 0;
    const rate = progress.processing_rate || 0;
    const eta = progress.estimated_remaining_seconds || 0;

    return (
      <Box
        p={6}
        borderRadius="16px"
        background={colorMode === 'dark'
          ? 'rgba(77, 124, 178, 0.1)'
          : 'rgba(77, 124, 178, 0.05)'}
        border="1px solid"
        borderColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.3)' : 'rgba(77, 124, 178, 0.2)'}
      >
        <VStack spacing={4}>
          <HStack spacing={8} justify="center" w="100%">
            <CircularProgress
              value={percent}
              size="120px"
              thickness="8px"
              color="brand.500"
            >
              <CircularProgressLabel fontSize="xl" fontWeight="bold">
                {percent}%
              </CircularProgressLabel>
            </CircularProgress>

            <VStack align="start" spacing={2}>
              <Text fontSize="lg" fontWeight="bold">
                {progress.phase || 'Processing'}
              </Text>
              <Text fontSize="sm" color="gray.500">
                {progress.current_item || 'Fetching tickets...'}
              </Text>
            </VStack>
          </HStack>

          <Progress
            value={percent}
            size="sm"
            w="100%"
            borderRadius="full"
            colorScheme="brand"
            isAnimated
            hasStripe
          />

          <SimpleGrid columns={4} spacing={4} w="100%">
            <Stat>
              <StatLabel>Total</StatLabel>
              <StatNumber fontSize="2xl">{total}</StatNumber>
              <StatHelpText>tickets</StatHelpText>
            </Stat>

            <Stat>
              <StatLabel>Processed</StatLabel>
              <StatNumber fontSize="2xl">{processed}</StatNumber>
              <StatHelpText>{successful} successful</StatHelpText>
            </Stat>

            <Stat>
              <StatLabel>Rate</StatLabel>
              <StatNumber fontSize="2xl">{rate.toFixed(1)}</StatNumber>
              <StatHelpText>tickets/sec</StatHelpText>
            </Stat>

            <Stat>
              <StatLabel>ETA</StatLabel>
              <StatNumber fontSize="2xl">{formatTime(eta)}</StatNumber>
              <StatHelpText>remaining</StatHelpText>
            </Stat>
          </SimpleGrid>

          {failed > 0 && (
            <Alert status="warning" borderRadius="md">
              <AlertIcon />
              <AlertDescription>
                {failed} ticket{failed > 1 ? 's' : ''} failed to fetch
              </AlertDescription>
            </Alert>
          )}
        </VStack>
      </Box>
    );
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
          p={6}
          borderRadius="16px"
          background={colorMode === 'dark'
            ? 'linear-gradient(135deg, rgba(77, 124, 178, 0.1), rgba(99, 102, 241, 0.1))'
            : 'linear-gradient(135deg, rgba(77, 124, 178, 0.05), rgba(99, 102, 241, 0.05))'}
          border="2px solid"
          borderColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.3)' : 'rgba(77, 124, 178, 0.2)'}
          position="relative"
          overflow="hidden"
          _before={{
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: 'linear-gradient(90deg, #4d7cb2, #4d7cb2, #4d7cb2)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 3s linear infinite',
          }}
        >
          <HStack spacing={3} align="center" mb={3}>
            <Icon
              as={MdBugReport}
              boxSize={8}
              color={colorMode === 'dark' ? '#7ba8d1' : '#4d7cb2'}
            />
            <Box>
              <Text
                fontSize="2xl"
                fontWeight="700"
                color={colorMode === 'dark' ? 'white' : 'gray.900'}
                letterSpacing="-0.02em"
              >
                Fetch Jira Tickets
              </Text>
              <Text
                fontSize="sm"
                color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}
                fontWeight="500"
              >
                Enter ticket keys (comma or space separated) to fetch and store
              </Text>
            </Box>
          </HStack>
        </Box>

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>Jira Ticket Keys</FormLabel>
              <Textarea
                value={jiraInput}
                onChange={(e) => setJiraInput(e.target.value)}
                placeholder="NEXUS-50206 NEXUS-50393&#10;or&#10;NEXUS-50206, NEXUS-50393"
                rows={4}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Collection Name</FormLabel>
              <Input
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                placeholder="jira_tickets"
              />
            </FormControl>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={MdBugReport} />}
              isLoading={isLoading}
              loadingText="Fetching..."
            >
              Fetch & Store Tickets
            </Button>
          </VStack>
        </form>

        {isLoading && !progress && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text color="rgba(255,255,255,0.7)">Starting...</Text>
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

        {isLoading && progress && renderProgressBar()}

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

export default JiraTab;

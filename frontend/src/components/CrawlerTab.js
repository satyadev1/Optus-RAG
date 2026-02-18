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
  Progress,
  List,
  ListItem,
  ListIcon,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  SimpleGrid,
  useColorModeValue,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from '@chakra-ui/react';
import { FiGlobe } from 'react-icons/fi';
import { CheckCircleIcon } from '@chakra-ui/icons';
import axios from 'axios';

function CrawlerTab() {
  const [startUrl, setStartUrl] = useState('');
  const [collection, setCollection] = useState('website_crawl');
  const [maxPages, setMaxPages] = useState(50);
  const [maxDepth, setMaxDepth] = useState(3);
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [crawlStats, setCrawlStats] = useState(null);
  const [estimatedTime, setEstimatedTime] = useState(0);

  const descColor = 'rgba(255,255,255,0.7)';
  const estimateBg = 'rgba(77,124,178,0.1)';
  const estimateBorder = 'rgba(77,124,178,0.3)';
  const estimateText = 'rgba(165,180,252,1)';
  const estimateSubtext = 'rgba(255,255,255,0.6)';
  const statBg = 'rgba(255,255,255,0.08)';
  const comparisonBg = 'rgba(16,185,129,0.1)';
  const comparisonBorder = 'rgba(16,185,129,0.3)';
  const comparisonLabelColor = 'rgba(255,255,255,0.7)';
  const comparisonValueColor = 'rgba(110,231,183,1)';
  const comparisonTextColor = 'rgba(255,255,255,0.6)';

  // Calculate estimated time whenever max_pages changes
  React.useEffect(() => {
    // Average 1.5 seconds per page (1s delay + 0.5s processing)
    const timePerPage = 1.5;
    const estimated = Math.ceil(maxPages * timePerPage);
    setEstimatedTime(estimated);
  }, [maxPages]);

  // Format time in a human-readable way
  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds} seconds`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return secs > 0 ? `${minutes}m ${secs}s` : `${minutes} minutes`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours} hours`;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!startUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a website URL' });
      return;
    }

    setIsLoading(true);
    setMessage(null);
    setCrawlStats(null);

    try {
      const response = await axios.post('/crawl_website', {
        start_url: startUrl,
        collection: collection,
        max_pages: maxPages,
        max_depth: maxDepth,
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: response.data.message
        });
        setCrawlStats(response.data.stats);
        setStartUrl('');
      } else {
        setMessage({
          type: 'error',
          text: response.data.message
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Error crawling website. Please check the URL and try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box>
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
            🌐 Website Crawler - Full Site Analysis
          </Text>
          <Text color={descColor}>
            Crawl entire websites and store all pages for AI analysis
          </Text>
        </Box>

        <Alert status="info" borderRadius="20px">
          <AlertIcon />
          <Box flex="1">
            <Text fontWeight="bold" mb={1}>Comprehensive Website Crawling</Text>
            <List spacing={1} fontSize="md">
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Recursively crawls all pages on the domain
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Extracts clean content from each page
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Respects rate limits and robots.txt
              </ListItem>
              <ListItem>
                <ListIcon as={CheckCircleIcon} color="green.500" />
                Stores in Milvus for semantic search
              </ListItem>
            </List>
          </Box>
        </Alert>

        <Alert status="warning" borderRadius="20px">
          <AlertIcon />
          <Box flex="1" fontSize="md">
            <Text fontWeight="bold">Important Notes:</Text>
            <Text>• Crawling will take time depending on site size (1-2 seconds per page)</Text>
            <Text>• Only pages from the same domain will be crawled</Text>
            <Text>• Large sites (100+ pages) may take several minutes</Text>
          </Box>
        </Alert>

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>Website URL</FormLabel>
              <Input
                value={startUrl}
                onChange={(e) => setStartUrl(e.target.value)}
                placeholder="https://docs.example.com/"
                type="url"
                size="lg"
              />
              <Text fontSize="md" color={descColor} mt={1}>
                Start from the homepage or any page - crawler will find all linked pages
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel>Collection Name</FormLabel>
              <Input
                value={collection}
                onChange={(e) => setCollection(e.target.value)}
                placeholder="website_crawl"
              />
              <Text fontSize="md" color={descColor} mt={1}>
                Name for organizing crawled pages in Milvus
              </Text>
            </FormControl>

            <SimpleGrid columns={2} spacing={4}>
              <FormControl>
                <FormLabel>Max Pages</FormLabel>
                <NumberInput
                  value={maxPages}
                  onChange={(valueString) => setMaxPages(parseInt(valueString) || 50)}
                  min={1}
                  max={1000}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
                <Text fontSize="md" color={descColor} mt={1}>
                  Maximum number of pages to crawl
                </Text>
                <Box mt={2} p={2} bg={estimateBg} borderRadius="20px" borderWidth={1} borderColor={estimateBorder}>
                  <Text fontSize="md" fontWeight="bold" color={estimateText}>
                    ⏱️ Estimated Time: {formatTime(estimatedTime)}
                  </Text>
                  <Text fontSize="md" color={estimateSubtext}>
                    ~1.5 seconds per page
                  </Text>
                </Box>
              </FormControl>

              <FormControl>
                <FormLabel>Max Depth</FormLabel>
                <NumberInput
                  value={maxDepth}
                  onChange={(valueString) => setMaxDepth(parseInt(valueString) || 3)}
                  min={1}
                  max={10}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
                <Text fontSize="md" color={descColor} mt={1}>
                  How many links deep to follow
                </Text>
              </FormControl>
            </SimpleGrid>

            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              leftIcon={<Icon as={FiGlobe} />}
              isLoading={isLoading}
              loadingText={`Crawling... (~${formatTime(estimatedTime)} estimated)`}
            >
              🚀 Start Crawling (Est. {formatTime(estimatedTime)})
            </Button>
            <Text fontSize="md" color="gray.500" textAlign="center">
              Crawl will take approximately {formatTime(estimatedTime)} at 1.5s per page
            </Text>
          </VStack>
        </form>

        {isLoading && (
          <Box py={8}>
            <Center mb={4}>
              <VStack>
                <Spinner size="xl" color="brand.500" thickness="4px" />
                <Text color="rgba(255,255,255,0.7)" fontWeight="bold">
                  Crawling in progress...
                </Text>
                <Text fontSize="md" color="brand.600" fontWeight="bold" mt={2}>
                  ⏱️ Estimated Time: {formatTime(estimatedTime)}
                </Text>
                <Text fontSize="md" color="gray.500">
                  Crawling up to {maxPages} pages with {maxDepth} depth levels
                </Text>
                <Text fontSize="md" color="gray.400" mt={2}>
                  Please wait... This process respects rate limits
                </Text>
              </VStack>
            </Center>
            <Progress size="sm" isIndeterminate colorScheme="brand" />
          </Box>
        )}

        {message && (
          <Alert status={message.type} borderRadius="20px">
            <AlertIcon />
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        {crawlStats && (
          <Box p={6} borderWidth={2} borderRadius="20px" borderColor="rgba(255,255,255,0.15)">
            <Text fontSize="lg" fontWeight="bold" mb={4} color="green.600">
              ✓ Crawl Completed Successfully
            </Text>

            <StatGroup>
              <Stat bg={statBg} p={4} borderRadius="20px" mr={2}>
                <StatLabel>Pages Crawled</StatLabel>
                <StatNumber color="blue.500">{crawlStats.pages_crawled}</StatNumber>
              </Stat>

              <Stat bg={statBg} p={4} borderRadius="20px" mr={2}>
                <StatLabel>Pages Stored</StatLabel>
                <StatNumber color="green.500">{crawlStats.pages_stored}</StatNumber>
              </Stat>

              <Stat bg={statBg} p={4} borderRadius="20px" mr={2}>
                <StatLabel>Failed</StatLabel>
                <StatNumber color="red.500">{crawlStats.pages_failed}</StatNumber>
              </Stat>

              <Stat bg={statBg} p={4} borderRadius="20px">
                <StatLabel>Actual Time</StatLabel>
                <StatNumber color="blue.600">{formatTime(Math.ceil(crawlStats.elapsed_time))}</StatNumber>
              </Stat>
            </StatGroup>

            <Box mt={4} p={3} bg={comparisonBg} borderRadius="20px" borderWidth={1} borderColor={comparisonBorder}>
              <SimpleGrid columns={2} spacing={4}>
                <Box>
                  <Text fontSize="md" fontWeight="bold" color={comparisonLabelColor}>
                    ⏱️ Estimated Time
                  </Text>
                  <Text fontSize="md" fontWeight="bold" color={comparisonValueColor}>
                    {formatTime(Math.ceil(crawlStats.pages_crawled * 1.5))}
                  </Text>
                </Box>
                <Box>
                  <Text fontSize="md" fontWeight="bold" color={comparisonLabelColor}>
                    ⚡ Actual Time
                  </Text>
                  <Text fontSize="md" fontWeight="bold" color={comparisonValueColor}>
                    {formatTime(Math.ceil(crawlStats.elapsed_time))}
                  </Text>
                </Box>
              </SimpleGrid>
              <Text fontSize="md" color={comparisonTextColor} mt={2}>
                {crawlStats.elapsed_time < (crawlStats.pages_crawled * 1.5)
                  ? `✓ Completed ${Math.round(((crawlStats.pages_crawled * 1.5) - crawlStats.elapsed_time) / (crawlStats.pages_crawled * 1.5) * 100)}% faster than expected`
                  : `Took ${Math.round((crawlStats.elapsed_time - (crawlStats.pages_crawled * 1.5)) / (crawlStats.pages_crawled * 1.5) * 100)}% longer (site may be slow or complex)`
                }
              </Text>
            </Box>

            <Box mt={4} p={3} backdropFilter="blur(8px)" background="rgba(100,200,255,0.08)" borderRadius="20px">
              <Text fontSize="md">
                <strong>Collection:</strong> {crawlStats.collection}
              </Text>
              <Text fontSize="md">
                <strong>Source:</strong> {crawlStats.start_url}
              </Text>
            </Box>

            <Alert status="success" mt={4} borderRadius="20px">
              <AlertIcon />
              <Box fontSize="md">
                Pages are now searchable via Claude AI and Ollama AI tabs.
                Select the collection "{crawlStats.collection}" to query the crawled content.
              </Box>
            </Alert>
          </Box>
        )}
      </VStack>
    </Box>
  );
}

export default CrawlerTab;

import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Button,
  Select,
  Divider,
  Progress,
  Icon,
  Spinner,
  Center,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useColorMode,
  Alert,
  AlertIcon,
  Tooltip,
  IconButton,
} from '@chakra-ui/react';
import { FiDownload, FiDollarSign, FiActivity, FiClock, FiDatabase, FiRefreshCw } from 'react-icons/fi';
import axios from 'axios';

function TokenUsageTab() {
  const { colorMode } = useColorMode();
  const [period, setPeriod] = useState('all');
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [costBreakdown, setCostBreakdown] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);

  const bgColor = colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.7)';
  const borderColor = colorMode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(100,116,139,0.2)';

  // Initial fetch
  useEffect(() => {
    fetchTokenStats();
    fetchCostBreakdown();
  }, [period]);

  const fetchTokenStats = async () => {
    setIsLoading(true);

    try {
      const response = await axios.get(`/token_usage/stats?period=${period}&limit=50`);
      if (response.data.success) {
        setStats(response.data.stats);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Error fetching token stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCostBreakdown = async () => {
    try {
      const breakdownPeriod = period === 'today' ? 'week' : period === 'all' ? 'month' : period;
      const response = await axios.get(`/token_usage/cost_breakdown?period=${breakdownPeriod}`);
      if (response.data.success) {
        setCostBreakdown(response.data.breakdown);
      }
    } catch (error) {
      console.error('Error fetching cost breakdown:', error);
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get(`/token_usage/export?period=${period}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `token_usage_${period}_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const formatCost = (cost) => {
    return `$${(cost || 0).toFixed(4)}`;
  };

  const formatNumber = (num) => {
    return (num || 0).toLocaleString();
  };

  const formatTime = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}min`;
  };

  const getTimeAgo = (date) => {
    if (!date) return '';
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 10) return 'just now';
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };

  if (isLoading && !stats) {
    return (
      <Center py={20}>
        <VStack spacing={4}>
          <Spinner size="xl" color="blue.600" thickness="4px" />
          <Text>Loading token usage data...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box
          backdropFilter="blur(8px)"
          background={bgColor}
          border="1px solid"
          borderColor={borderColor}
          borderRadius="20px"
          p={6}
          transition="all 300ms ease-in-out"
        >
          <HStack justify="space-between" mb={4}>
            <Box>
              <HStack spacing={3} align="center">
                <Text fontSize="2xl" fontWeight="700" color={colorMode === 'dark' ? 'white' : '#1e293b'}>
                  💰 Token Usage & Cost Tracking
                </Text>
                {lastUpdate && (
                  <Badge
                    colorScheme="green"
                    fontSize="xs"
                    px={2}
                    py={1}
                  >
                    Updated {getTimeAgo(lastUpdate)}
                  </Badge>
                )}
              </HStack>
              <Text fontSize="sm" color="gray.500" mt={1}>
                Monitor Claude API usage, costs, and performance metrics
              </Text>
            </Box>
            <HStack spacing={3}>
              <Select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                size="sm"
                w="150px"
              >
                <option value="today">Today</option>
                <option value="week">Last 7 Days</option>
                <option value="month">Last 30 Days</option>
                <option value="all">All Time</option>
              </Select>
              <Tooltip label="Refresh data">
                <Button
                  leftIcon={<FiRefreshCw />}
                  colorScheme="blue"
                  size="sm"
                  onClick={() => {
                    fetchTokenStats();
                    fetchCostBreakdown();
                  }}
                  isLoading={isLoading}
                >
                  Refresh
                </Button>
              </Tooltip>
              <Button
                leftIcon={<FiDownload />}
                colorScheme="blue"
                size="sm"
                onClick={handleExport}
              >
                Export CSV
              </Button>
            </HStack>
          </HStack>
        </Box>

        {stats && stats.summary ? (
          <>
            {/* Key Metrics */}
            <StatGroup>
              <Stat
                backdropFilter="blur(8px)"
                background={bgColor}
                border="1px solid"
                borderColor={borderColor}
                borderRadius="20px"
                p={6}
              >
                <StatLabel fontSize="sm" fontWeight="600">
                  <Icon as={FiDollarSign} mr={2} />
                  Total Cost
                </StatLabel>
                <StatNumber fontSize="3xl" color="green.500">
                  {formatCost(stats.summary.total_cost)}
                </StatNumber>
                <StatHelpText>
                  {formatNumber(stats.summary.total_requests)} requests
                </StatHelpText>
              </Stat>

              <Stat
                backdropFilter="blur(8px)"
                background={bgColor}
                border="1px solid"
                borderColor={borderColor}
                borderRadius="20px"
                p={6}
              >
                <StatLabel fontSize="sm" fontWeight="600">
                  <Icon as={FiActivity} mr={2} />
                  Total Tokens
                </StatLabel>
                <StatNumber fontSize="3xl" color="blue.600">
                  {formatNumber(stats.summary.total_tokens)}
                </StatNumber>
                <StatHelpText>
                  {formatNumber(stats.summary.total_input_tokens)} in + {formatNumber(stats.summary.total_output_tokens)} out
                </StatHelpText>
              </Stat>

              <Stat
                backdropFilter="blur(8px)"
                background={bgColor}
                border="1px solid"
                borderColor={borderColor}
                borderRadius="20px"
                p={6}
              >
                <StatLabel fontSize="sm" fontWeight="600">
                  <Icon as={FiClock} mr={2} />
                  Avg Response Time
                </StatLabel>
                <StatNumber fontSize="3xl" color="blue.500">
                  {formatTime(stats.summary.avg_response_time || 0)}
                </StatNumber>
                <StatHelpText>
                  {stats.summary.successful_requests} successful
                </StatHelpText>
              </Stat>

              <Stat
                backdropFilter="blur(8px)"
                background={bgColor}
                border="1px solid"
                borderColor={borderColor}
                borderRadius="20px"
                p={6}
              >
                <StatLabel fontSize="sm" fontWeight="600">
                  <Icon as={FiDatabase} mr={2} />
                  Documents Retrieved
                </StatLabel>
                <StatNumber fontSize="3xl" color="orange.500">
                  {formatNumber(stats.summary.total_documents)}
                </StatNumber>
                <StatHelpText>
                  Avg {(stats.summary.total_documents / stats.summary.total_requests || 0).toFixed(1)} per query
                </StatHelpText>
              </Stat>
            </StatGroup>

            <Divider />

            {/* Tabs for different views */}
            <Tabs variant="soft-rounded" colorScheme="blue">
              <TabList>
                <Tab>Recent Queries</Tab>
                <Tab>Model Breakdown</Tab>
                <Tab>Collection Breakdown</Tab>
                <Tab>Cost Trend</Tab>
              </TabList>

              <TabPanels>
                {/* Recent Queries Tab */}
                <TabPanel>
                  <Box
                    backdropFilter="blur(8px)"
                    background={bgColor}
                    border="1px solid"
                    borderColor={borderColor}
                    borderRadius="20px"
                    p={6}
                    overflowX="auto"
                  >
                    <Text fontSize="lg" fontWeight="bold" mb={4}>
                      📝 Recent Queries ({stats.recent_queries.length})
                    </Text>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Timestamp</Th>
                          <Th>Question</Th>
                          <Th>Collection</Th>
                          <Th isNumeric>Tokens</Th>
                          <Th isNumeric>Cost</Th>
                          <Th isNumeric>Time</Th>
                          <Th>Status</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {stats.recent_queries.map((query, index) => (
                          <Tr key={index}>
                            <Td fontSize="xs">
                              {new Date(query.timestamp).toLocaleString()}
                            </Td>
                            <Td maxW="300px" isTruncated title={query.question}>
                              {query.question}
                            </Td>
                            <Td>
                              <Badge colorScheme="blue" fontSize="xs">
                                {query.collection}
                              </Badge>
                            </Td>
                            <Td isNumeric fontSize="xs">
                              {formatNumber(query.total_tokens)}
                            </Td>
                            <Td isNumeric fontSize="xs" fontWeight="600" color="green.500">
                              {formatCost(query.cost_usd)}
                            </Td>
                            <Td isNumeric fontSize="xs">
                              {formatTime(query.response_time_ms)}
                            </Td>
                            <Td>
                              <Badge colorScheme={query.success ? 'green' : 'red'} fontSize="xs">
                                {query.success ? '✓' : '✗'}
                              </Badge>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                </TabPanel>

                {/* Model Breakdown Tab */}
                <TabPanel>
                  <Box
                    backdropFilter="blur(8px)"
                    background={bgColor}
                    border="1px solid"
                    borderColor={borderColor}
                    borderRadius="20px"
                    p={6}
                  >
                    <Text fontSize="lg" fontWeight="bold" mb={4}>
                      🤖 Usage by Model
                    </Text>
                    <VStack spacing={4} align="stretch">
                      {stats.model_breakdown.map((model, index) => (
                        <Box
                          key={index}
                          p={4}
                          borderRadius="12px"
                          border="1px solid"
                          borderColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.3)' : 'rgba(77, 124, 178, 0.3)'}
                          _hover={{
                            borderColor: colorMode === 'dark' ? 'rgba(77, 124, 178, 0.5)' : 'rgba(77, 124, 178, 0.5)',
                          }}
                        >
                          <HStack justify="space-between" mb={2}>
                            <Text fontWeight="600">{model.model}</Text>
                            <Badge colorScheme="blue">{model.requests} requests</Badge>
                          </HStack>
                          <HStack spacing={6}>
                            <Text fontSize="sm">Tokens: {formatNumber(model.tokens)}</Text>
                            <Text fontSize="sm" fontWeight="600" color="green.500">
                              Cost: {formatCost(model.cost)}
                            </Text>
                          </HStack>
                        </Box>
                      ))}
                    </VStack>
                  </Box>
                </TabPanel>

                {/* Collection Breakdown Tab */}
                <TabPanel>
                  <Box
                    backdropFilter="blur(8px)"
                    background={bgColor}
                    border="1px solid"
                    borderColor={borderColor}
                    borderRadius="20px"
                    p={6}
                  >
                    <Text fontSize="lg" fontWeight="bold" mb={4}>
                      📚 Usage by Collection
                    </Text>
                    <VStack spacing={4} align="stretch">
                      {stats.collection_breakdown.map((coll, index) => (
                        <Box
                          key={index}
                          p={4}
                          borderRadius="12px"
                          border="1px solid"
                          borderColor={colorMode === 'dark' ? 'rgba(59, 130, 246, 0.3)' : 'rgba(59, 130, 246, 0.3)'}
                          _hover={{
                            borderColor: colorMode === 'dark' ? 'rgba(59, 130, 246, 0.5)' : 'rgba(59, 130, 246, 0.5)',
                          }}
                        >
                          <HStack justify="space-between" mb={2}>
                            <Text fontWeight="600">{coll.collection}</Text>
                            <Badge colorScheme="blue">{coll.requests} requests</Badge>
                          </HStack>
                          <HStack spacing={6}>
                            <Text fontSize="sm">Tokens: {formatNumber(coll.tokens)}</Text>
                            <Text fontSize="sm" fontWeight="600" color="green.500">
                              Cost: {formatCost(coll.cost)}
                            </Text>
                          </HStack>
                          <Progress
                            value={(coll.cost / stats.summary.total_cost) * 100}
                            size="sm"
                            colorScheme="blue"
                            mt={2}
                            borderRadius="full"
                          />
                        </Box>
                      ))}
                    </VStack>
                  </Box>
                </TabPanel>

                {/* Cost Trend Tab */}
                <TabPanel>
                  <Box
                    backdropFilter="blur(8px)"
                    background={bgColor}
                    border="1px solid"
                    borderColor={borderColor}
                    borderRadius="20px"
                    p={6}
                  >
                    <Text fontSize="lg" fontWeight="bold" mb={4}>
                      📈 Daily Cost Trend
                    </Text>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Date</Th>
                          <Th isNumeric>Requests</Th>
                          <Th isNumeric>Tokens</Th>
                          <Th isNumeric>Cost</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {costBreakdown.map((day, index) => (
                          <Tr key={index}>
                            <Td>{day.date}</Td>
                            <Td isNumeric>{formatNumber(day.requests)}</Td>
                            <Td isNumeric>{formatNumber(day.tokens)}</Td>
                            <Td isNumeric fontWeight="600" color="green.500">
                              {formatCost(day.cost)}
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                </TabPanel>
              </TabPanels>
            </Tabs>

            {/* Info Alert */}
            <Alert status="info" borderRadius="20px">
              <AlertIcon />
              <Box flex="1">
                <Text fontWeight="bold" mb={1}>Token Tracking Info</Text>
                <Text fontSize="sm">
                  Pricing: Claude Sonnet 4.5 = $3/MTok input + $15/MTok output • All queries are automatically tracked for audit purposes
                </Text>
              </Box>
            </Alert>
          </>
        ) : (
          <Alert status="warning" borderRadius="20px">
            <AlertIcon />
            <Text>No token usage data available yet. Start asking questions to see statistics!</Text>
          </Alert>
        )}
      </VStack>
    </Box>
  );
}

export default TokenUsageTab;

import React, { useState, useEffect } from 'react';
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
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Divider,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import { AiOutlineGithub } from 'react-icons/ai';
import { DownloadIcon } from '@chakra-ui/icons';
import axios from 'axios';
import AnimatedSelect from './AnimatedSelect';

function RepoAnalyzerTab() {
  const [repoUrl, setRepoUrl] = useState('');

  const descColor = "rgba(255,255,255,0.7)";
  const bgColor = "rgba(255,255,255,0.08)";
  const borderColor = "rgba(255,255,255,0.15)";
  const hoverBg = "rgba(255,255,255,0.12)";
  const [prLimit, setPrLimit] = useState('100');
  const [state, setState] = useState('all');
  const [collection, setCollection] = useState('github_prs');
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [stats, setStats] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [trackedPRs, setTrackedPRs] = useState([]);

  useEffect(() => {
    // Fetch tracked PRs when stats are available
    if (stats && stats.repository) {
      fetchTrackedPRs(stats.repository);
    }
  }, [stats]);

  const fetchTrackedPRs = async (repository) => {
    try {
      const response = await axios.get(`/get_analyzed_prs?repository=${encodeURIComponent(repository)}`);
      if (response.data.success) {
        const allPRs = [
          ...response.data.tracked_prs.successful,
          ...response.data.tracked_prs.failed
        ];
        setTrackedPRs(allPRs);
      }
    } catch (error) {
      console.error('Error fetching tracked PRs:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a GitHub repository URL' });
      return;
    }

    setIsLoading(true);
    setMessage(null);
    setStats(null);
    setPersonas([]);
    setLoadingStatus('Fetching PRs from repository...');

    try {
      const response = await axios.post('/fetch_repo_prs', {
        repo_url: repoUrl,
        pr_limit: prLimit,
        state: state,
        collection: collection,
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: response.data.message,
        });
        setStats(response.data.stats);
        setPersonas(response.data.persona_result?.personas || []);
      } else {
        setMessage({
          type: 'error',
          text: response.data.message,
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.message || 'Error fetching repository PRs'
      });
    } finally {
      setIsLoading(false);
      setLoadingStatus('');
    }
  };

  const handleExportAllPDF = async () => {
    try {
      const response = await axios.get('/export_all_personas_pdf', {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `personas_summary_${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setMessage({ type: 'error', text: 'Error exporting PDF' });
    }
  };


  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Box>
          <Text fontSize="xl" fontWeight="bold" mb={2}>
            🔍 GitHub Repository Analyzer
          </Text>
          <Text color={descColor}>
            Fetch all PRs from a repository and analyze contributor patterns
          </Text>
        </Box>

        <Alert status="info" borderRadius="20px">
          <AlertIcon />
          <Box flex="1">
            <Text fontWeight="bold" mb={1}>Comprehensive Repository Analysis</Text>
            <Text fontSize="md">
              Fetches all PRs with complete details (reviews, comments, commits) and automatically
              builds contributor personas with approval patterns, merge authority, and collaboration graphs
            </Text>
          </Box>
        </Alert>

        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>GitHub Repository URL</FormLabel>
              <Input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                type="url"
              />
            </FormControl>

            <HStack spacing={4} align="flex-end">
              <FormControl isRequired>
                <FormLabel>Number of PRs to Analyze</FormLabel>
                <Input
                  value={prLimit}
                  onChange={(e) => setPrLimit(e.target.value)}
                  placeholder="Enter number (e.g., 100) or * for all"
                  type="text"
                />
                <Text fontSize="md" color="gray.500" mt={1}>
                  Enter a number (e.g., 50, 100, 500) or use * to fetch all PRs
                </Text>
              </FormControl>

              <FormControl maxW="200px">
                <FormLabel>PR State</FormLabel>
                <AnimatedSelect
                  value={state}
                  onChange={setState}
                  size="sm"
                  placeholder="Select State"
                  options={[
                    { value: 'all', label: '📋 All' },
                    { value: 'open', label: '✅ Open' },
                    { value: 'closed', label: '🔒 Closed' },
                  ]}
                />
              </FormControl>
            </HStack>

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
              loadingText="Fetching PRs..."
            >
              🚀 Fetch All PRs & Analyze
            </Button>
          </VStack>
        </form>

        {isLoading && (
          <Center py={8}>
            <VStack spacing={4} w="100%">
              <Spinner size="xl" color="brand.500" thickness="4px" />
              <Text fontWeight="bold" color="rgba(255,255,255,0.7)">{loadingStatus}</Text>
              <Progress
                w="80%"
                size="sm"
                isIndeterminate
                colorScheme="brand"
                borderRadius="20px"
              />
              <Text fontSize="md" color="gray.500">
                This may take several minutes for large repositories...
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

        {stats && (
          <>
            <Divider />

            <Box p={6} bg={bgColor} borderRadius="20px">
              <Text fontSize="lg" fontWeight="bold" mb={4}>
                📊 Summary Statistics
              </Text>
              <HStack spacing={8} flexWrap="wrap">
                <Box>
                  <Text fontSize="md" color={descColor}>Repository</Text>
                  <Text fontSize="md" fontWeight="bold">{stats.repository}</Text>
                </Box>
                <Box>
                  <Text fontSize="md" color={descColor}>Total PRs</Text>
                  <Text fontSize="md" fontWeight="bold">{stats.total_prs}</Text>
                </Box>
                <Box>
                  <Text fontSize="md" color={descColor}>Stored</Text>
                  <Text fontSize="md" fontWeight="bold" color="green.500">
                    {stats.stored_prs}
                  </Text>
                </Box>
                <Box>
                  <Text fontSize="md" color={descColor}>Failed</Text>
                  <Text fontSize="md" fontWeight="bold" color="red.500">
                    {stats.failed_prs}
                  </Text>
                </Box>
                {stats.skipped_prs > 0 && (
                  <Box>
                    <Text fontSize="md" color={descColor}>Skipped</Text>
                    <Text fontSize="md" fontWeight="bold" color="orange.500">
                      {stats.skipped_prs}
                    </Text>
                  </Box>
                )}
                <Box>
                  <Text fontSize="md" color={descColor}>Personas Built</Text>
                  <Text fontSize="md" fontWeight="bold" color="blue.600">
                    {stats.personas_built}
                  </Text>
                </Box>
              </HStack>
            </Box>

            {personas.length > 0 && (
              <>
                <Box>
                  <HStack justify="space-between" mb={4}>
                    <Text fontSize="lg" fontWeight="bold">
                      👥 Contributor Personas ({personas.length})
                    </Text>
                    <Button
                      leftIcon={<DownloadIcon />}
                      colorScheme="blue"
                      size="sm"
                      onClick={handleExportAllPDF}
                    >
                      Export All as PDF
                    </Button>
                  </HStack>

                  <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Username</Th>
                          <Th>Role</Th>
                          <Th isNumeric>PRs Authored</Th>
                          <Th isNumeric>PRs Reviewed</Th>
                          <Th isNumeric>Approvals</Th>
                          <Th isNumeric>PRs Merged</Th>
                          <Th isNumeric>Approval Rate</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {personas
                          .sort((a, b) => b.statistics.prs_reviewed - a.statistics.prs_reviewed)
                          .map((persona) => (
                            <Tr key={persona.username}>
                              <Td fontWeight="medium">{persona.username}</Td>
                              <Td>
                                <Badge
                                  colorScheme={
                                    persona.role === 'maintainer'
                                      ? 'purple'
                                      : persona.role === 'reviewer'
                                      ? 'blue'
                                      : persona.role === 'contributor'
                                      ? 'green'
                                      : 'gray'
                                  }
                                >
                                  {persona.role}
                                </Badge>
                              </Td>
                              <Td isNumeric>{persona.statistics.prs_authored}</Td>
                              <Td isNumeric>{persona.statistics.prs_reviewed}</Td>
                              <Td isNumeric>{persona.statistics.approvals_given}</Td>
                              <Td isNumeric>{persona.statistics.prs_merged}</Td>
                              <Td isNumeric>
                                {(persona.statistics.approval_rate * 100).toFixed(0)}%
                              </Td>
                            </Tr>
                          ))}
                      </Tbody>
                    </Table>
                  </Box>
                </Box>

                <Alert status="success" borderRadius="20px">
                  <AlertIcon />
                  <Box flex="1">
                    <Text fontWeight="bold" mb={1}>Next Steps</Text>
                    <Text fontSize="md">
                      Go to the "Personas" tab to view detailed analysis, export individual
                      reports, and query specific contributor patterns
                    </Text>
                  </Box>
                </Alert>
              </>
            )}

            {trackedPRs.length > 0 && (
              <>
                <Divider />

                <Box>
                  <Text fontSize="lg" fontWeight="bold" mb={4}>
                    📋 Analyzed PRs ({trackedPRs.length})
                  </Text>

                  <Accordion allowToggle>
                    <AccordionItem>
                      <AccordionButton>
                        <Box flex="1" textAlign="left">
                          <Text fontWeight="bold">View All Analyzed PRs</Text>
                        </Box>
                        <AccordionIcon />
                      </AccordionButton>
                      <AccordionPanel pb={4}>
                        <Box overflowX="auto">
                          <Table variant="simple" size="sm">
                            <Thead>
                              <Tr>
                                <Th>PR Number</Th>
                                <Th>Title</Th>
                                <Th>Status</Th>
                                <Th>Fetched At</Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {trackedPRs
                                .sort((a, b) => b.pr_number - a.pr_number)
                                .map((pr) => (
                                  <Tr key={pr.pr_number}>
                                    <Td>#{pr.pr_number}</Td>
                                    <Td maxW="300px" isTruncated>{pr.pr_title}</Td>
                                    <Td>
                                      <Badge
                                        colorScheme={pr.status === 'success' ? 'green' : 'red'}
                                      >
                                        {pr.status}
                                      </Badge>
                                    </Td>
                                    <Td fontSize="md" color="gray.500">
                                      {new Date(pr.fetched_at).toLocaleString()}
                                    </Td>
                                  </Tr>
                                ))}
                            </Tbody>
                          </Table>
                        </Box>
                      </AccordionPanel>
                    </AccordionItem>
                  </Accordion>
                </Box>
              </>
            )}
          </>
        )}
      </VStack>
    </Box>
  );
}

export default RepoAnalyzerTab;

import React, { useState, useEffect } from 'react';
import {
  VStack,
  HStack,
  Box,
  Text,
  Button,
  Alert,
  AlertIcon,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Center,
  Collapse,
  useDisclosure,
  Input,
  InputGroup,
  InputLeftElement,
  Divider,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
} from '@chakra-ui/react';
import { SearchIcon, DownloadIcon, ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import axios from 'axios';

function PersonaTab() {
  const [personas, setPersonas] = useState([]);
  const [filteredPersonas, setFilteredPersonas] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const { isOpen, onToggle } = useDisclosure();

  const bgColor = 'rgba(255,255,255,0.08)';
  const borderColor = 'rgba(255,255,255,0.15)';
  const hoverBg = 'rgba(255,255,255,0.12)';

  useEffect(() => {
    fetchPersonas();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredPersonas(personas);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = personas.filter(
        (p) =>
          p.username.toLowerCase().includes(query) ||
          p.role.toLowerCase().includes(query) ||
          (p.statistics.prs_reviewed > 0 && query.includes('reviewer')) ||
          (p.statistics.prs_merged > 10 && query.includes('maintainer'))
      );
      setFilteredPersonas(filtered);
    }
  }, [searchQuery, personas]);

  const fetchPersonas = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/get_all_personas');
      if (response.data.success) {
        setPersonas(response.data.personas);
        setFilteredPersonas(response.data.personas);
      } else {
        setMessage({ type: 'error', text: response.data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error fetching personas' });
    } finally {
      setIsLoading(false);
    }
  };

  const viewPersonaDetails = async (username) => {
    try {
      const response = await axios.get(`/get_persona/${username}`);
      if (response.data.success) {
        setSelectedPersona(response.data.persona);
        onToggle();
      } else {
        setMessage({ type: 'error', text: response.data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error fetching persona details' });
    }
  };

  const exportPersonaPDF = async (username) => {
    try {
      const response = await axios.get(`/export_persona_pdf/${username}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `persona_report_${username}_${new Date().toISOString().split('T')[0]}.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setMessage({ type: 'error', text: 'Error exporting PDF' });
    }
  };

  const exportAllPDF = async () => {
    try {
      const response = await axios.get('/export_all_personas_pdf', {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `personas_summary_${new Date().toISOString().split('T')[0]}.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setMessage({ type: 'error', text: 'Error exporting summary PDF' });
    }
  };

  if (isLoading) {
    return (
      <Center h="400px">
        <VStack>
          <Spinner size="xl" color="brand.500" thickness="4px" />
          <Text color="rgba(255,255,255,0.7)">Loading personas...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Box>
          <HStack justify="space-between" mb={2}>
            <Text fontSize="xl" fontWeight="700" color={colorMode === 'dark' ? 'white' : '#1e293b'} letterSpacing="wide">
              👥 GitHub Personas ({personas.length})
            </Text>
            {personas.length > 0 && (
              <Button
                leftIcon={<DownloadIcon />}
                colorScheme="blue"
                size="sm"
                onClick={exportAllPDF}
              >
                Export All as PDF
              </Button>
            )}
          </HStack>
          <Text color="rgba(255,255,255,0.7)">
            Analyze contributor patterns, review styles, and collaboration networks
          </Text>
        </Box>

        {message && (
          <Alert status={message.type} borderRadius="20px">
            <AlertIcon />
            {message.text}
          </Alert>
        )}

        {personas.length === 0 ? (
          <Alert status="info" borderRadius="20px">
            <AlertIcon />
            <Box flex="1">
              <Text fontWeight="bold" mb={1}>No Personas Found</Text>
              <Text fontSize="md">
                Go to "Repository Analyzer" tab to fetch PRs and build personas
              </Text>
            </Box>
          </Alert>
        ) : (
          <>
            <InputGroup>
              <InputLeftElement pointerEvents="none">
                <SearchIcon color="gray.400" />
              </InputLeftElement>
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by username, role, or patterns..."
              />
            </InputGroup>

            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>
                      <VStack align="start" spacing={0}>
                        <Text>Username</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          GitHub handle
                        </Text>
                      </VStack>
                    </Th>
                    <Th>
                      <VStack align="start" spacing={0}>
                        <Text>Role</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          Based on activity
                        </Text>
                      </VStack>
                    </Th>
                    <Th isNumeric>
                      <VStack align="end" spacing={0}>
                        <Text>PRs</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          Authored
                        </Text>
                      </VStack>
                    </Th>
                    <Th isNumeric>
                      <VStack align="end" spacing={0}>
                        <Text>Reviews</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          Total reviewed
                        </Text>
                      </VStack>
                    </Th>
                    <Th isNumeric>
                      <VStack align="end" spacing={0}>
                        <Text>Approvals</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          PRs approved
                        </Text>
                      </VStack>
                    </Th>
                    <Th isNumeric>
                      <VStack align="end" spacing={0}>
                        <Text>Merges</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          PRs merged
                        </Text>
                      </VStack>
                    </Th>
                    <Th isNumeric>
                      <VStack align="end" spacing={0}>
                        <Text>Approval Rate</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          Approvals/Reviews
                        </Text>
                      </VStack>
                    </Th>
                    <Th>
                      <VStack align="start" spacing={0}>
                        <Text>Review Style</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          Quick/Balanced/Thorough
                        </Text>
                      </VStack>
                    </Th>
                    <Th>
                      <VStack align="start" spacing={0}>
                        <Text>Actions</Text>
                        <Text fontSize="md" fontWeight="normal" color="gray.500">
                          Export PDF
                        </Text>
                      </VStack>
                    </Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {filteredPersonas
                    .sort((a, b) => b.statistics.prs_reviewed - a.statistics.prs_reviewed)
                    .map((persona) => (
                      <Tr
                        key={persona.username}
                        _hover={{ bg: hoverBg }}
                        cursor="pointer"
                        onClick={() => viewPersonaDetails(persona.username)}
                      >
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
                        <Td>
                          <Badge variant="outline" colorScheme="teal" fontSize="md">
                            {persona.statistics.prs_reviewed > 0
                              ? persona.statistics.avg_comments_per_review > 3
                                ? 'thorough'
                                : persona.statistics.approval_rate > 0.8
                                ? 'quick'
                                : 'balanced'
                              : 'none'}
                          </Badge>
                        </Td>
                        <Td onClick={(e) => e.stopPropagation()}>
                          <Button
                            size="xs"
                            leftIcon={<DownloadIcon />}
                            colorScheme="blue"
                            variant="ghost"
                            onClick={() => exportPersonaPDF(persona.username)}
                          >
                            PDF
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                </Tbody>
              </Table>
            </Box>

            {selectedPersona && (
              <Box
                p={6}
                bg={bgColor}
                borderWidth="2px"
                borderColor={borderColor}
                borderRadius="20px"
                mt={4}
              >
                <HStack justify="space-between" mb={4}>
                  <Text fontSize="lg" fontWeight="bold">
                    📊 Detailed View: {selectedPersona.username}
                  </Text>
                  <Button
                    size="sm"
                    leftIcon={isOpen ? <ChevronUpIcon /> : <ChevronDownIcon />}
                    onClick={onToggle}
                  >
                    {isOpen ? 'Hide' : 'Show'} Details
                  </Button>
                </HStack>

                <Collapse in={isOpen} animateOpacity>
                  <VStack spacing={6} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                      <Stat>
                        <StatLabel>Role</StatLabel>
                        <StatNumber>
                          <Badge
                            colorScheme={
                              selectedPersona.role === 'maintainer'
                                ? 'purple'
                                : selectedPersona.role === 'reviewer'
                                ? 'blue'
                                : 'green'
                            }
                            fontSize="md"
                          >
                            {selectedPersona.role}
                          </Badge>
                        </StatNumber>
                        <StatHelpText>Inferred from activity</StatHelpText>
                      </Stat>

                      <Stat>
                        <StatLabel>Total Activity</StatLabel>
                        <StatNumber>
                          {selectedPersona.statistics.prs_authored +
                            selectedPersona.statistics.prs_reviewed}
                        </StatNumber>
                        <StatHelpText>PRs authored + reviewed</StatHelpText>
                      </Stat>

                      <Stat>
                        <StatLabel>Review Style</StatLabel>
                        <StatNumber fontSize="md">
                          {selectedPersona.patterns?.review_style?.replace('_', ' ') || 'N/A'}
                        </StatNumber>
                        <StatHelpText>
                          Tone: {selectedPersona.patterns?.tone || 'neutral'}
                        </StatHelpText>
                      </Stat>
                    </SimpleGrid>

                    <Divider />

                    <Box>
                      <Text fontWeight="bold" mb={3}>
                        Statistics
                      </Text>
                      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            PRs Authored
                          </Text>
                          <Text fontSize="xl" fontWeight="700" color="white" letterSpacing="wide">
                            {selectedPersona.statistics.prs_authored}
                          </Text>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            PRs Reviewed
                          </Text>
                          <Text fontSize="xl" fontWeight="700" color="white" letterSpacing="wide">
                            {selectedPersona.statistics.prs_reviewed}
                          </Text>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Approvals Given
                          </Text>
                          <Text fontSize="xl" fontWeight="700" color="green.500" letterSpacing="wide">
                            {selectedPersona.statistics.approvals_given}
                          </Text>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Changes Requested
                          </Text>
                          <Text fontSize="xl" fontWeight="700" color="orange.500" letterSpacing="wide">
                            {selectedPersona.statistics.changes_requested}
                          </Text>
                        </Box>
                      </SimpleGrid>
                    </Box>

                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        Merge Authority
                      </Text>
                      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Total PRs Merged
                          </Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {selectedPersona.statistics.prs_merged}
                          </Text>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Own PRs Merged
                          </Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {selectedPersona.statistics.prs_merged_own}
                          </Text>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Others' PRs Merged
                          </Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {selectedPersona.statistics.prs_merged_others}
                          </Text>
                        </Box>
                      </SimpleGrid>
                    </Box>

                    <Box>
                      <Text fontWeight="bold" mb={2}>
                        Rates & Averages
                      </Text>
                      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Approval Rate
                          </Text>
                          <HStack>
                            <Text fontSize="lg" fontWeight="bold">
                              {(selectedPersona.statistics.approval_rate * 100).toFixed(0)}%
                            </Text>
                            <Progress
                              value={selectedPersona.statistics.approval_rate * 100}
                              size="sm"
                              colorScheme="green"
                              flex="1"
                            />
                          </HStack>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Merge Rate
                          </Text>
                          <HStack>
                            <Text fontSize="lg" fontWeight="bold">
                              {(selectedPersona.statistics.merge_rate * 100).toFixed(0)}%
                            </Text>
                            <Progress
                              value={selectedPersona.statistics.merge_rate * 100}
                              size="sm"
                              colorScheme="blue"
                              flex="1"
                            />
                          </HStack>
                        </Box>
                        <Box>
                          <Text fontSize="md" color="rgba(255,255,255,0.7)">
                            Avg Comments/Review
                          </Text>
                          <Text fontSize="lg" fontWeight="bold">
                            {selectedPersona.statistics.avg_comments_per_review}
                          </Text>
                        </Box>
                      </SimpleGrid>
                    </Box>

                    {selectedPersona.patterns?.comment_types && (
                      <Box>
                        <Text fontWeight="bold" mb={2}>
                          Comment Topics
                        </Text>
                        <HStack spacing={2} flexWrap="wrap">
                          {Object.entries(selectedPersona.patterns.comment_types).map(
                            ([topic, count]) =>
                              count > 0 && (
                                <Badge key={topic} colorScheme="blue" fontSize="md">
                                  {topic.replace('_', ' ')}: {count}
                                </Badge>
                              )
                          )}
                        </HStack>
                      </Box>
                    )}

                    {selectedPersona.relationships?.frequently_reviews?.length > 0 && (
                      <Box>
                        <Text fontWeight="bold" mb={2}>
                          Frequently Reviews
                        </Text>
                        <HStack spacing={2} flexWrap="wrap">
                          {selectedPersona.relationships.frequently_reviews
                            .slice(0, 10)
                            .map((rel) => (
                              <Badge key={rel.username} colorScheme="teal" fontSize="md">
                                {rel.username} ({rel.count})
                              </Badge>
                            ))}
                        </HStack>
                      </Box>
                    )}

                    <Button
                      leftIcon={<DownloadIcon />}
                      colorScheme="blue"
                      onClick={() => exportPersonaPDF(selectedPersona.username)}
                    >
                      Export Full Report as PDF
                    </Button>
                  </VStack>
                </Collapse>
              </Box>
            )}
          </>
        )}
      </VStack>
    </Box>
  );
}

export default PersonaTab;

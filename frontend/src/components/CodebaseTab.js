import React, { useState, useEffect, useRef } from 'react';
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
  Progress,
  useColorMode,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Badge,
  Code,
  Divider,
  Checkbox,
  Link as ChakraLink,
  CircularProgress,
  CircularProgressLabel,
} from '@chakra-ui/react';
import { FiCode, FiFolder, FiFileText, FiSearch, FiGithub, FiRefreshCw, FiClock } from 'react-icons/fi';
import { AiOutlineCode } from 'react-icons/ai';
import axios from 'axios';

function CodebaseTab() {
  const { colorMode } = useColorMode();
  const [directory, setDirectory] = useState('');
  const [repoName, setRepoName] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [pullLatest, setPullLatest] = useState(true);
  const [isPrivate, setIsPrivate] = useState(false);
  const [privacyPassword, setPrivacyPassword] = useState('sdk');
  const [message, setMessage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [stats, setStats] = useState(null);

  // Progress state
  const [progress, setProgress] = useState(null);
  const [progressFile, setProgressFile] = useState(null);
  const progressIntervalRef = useRef(null);

  useEffect(() => {
    fetchStats();
    checkForOngoingAnalysis();
  }, []);

  const checkForOngoingAnalysis = () => {
    // Check localStorage for ongoing analysis
    const savedProgressFile = localStorage.getItem('codebase_progress_file');
    const savedIsAnalyzing = localStorage.getItem('codebase_is_analyzing');

    if (savedProgressFile && savedIsAnalyzing === 'true') {
      setProgressFile(savedProgressFile);
      setIsAnalyzing(true);
      setMessage({
        type: 'info',
        text: 'Resuming ongoing analysis...',
      });
    }
  };

  // Poll for progress updates
  useEffect(() => {
    if (isAnalyzing && progressFile) {
      // Start polling every 2 seconds
      progressIntervalRef.current = setInterval(() => {
        fetchProgress();
      }, 2000);

      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    }
  }, [isAnalyzing, progressFile]);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/codebase_stats');
      if (response.data.success) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchProgress = async () => {
    if (!progressFile) return;

    try {
      const response = await axios.get('/analysis_progress', {
        params: { progress_file: progressFile }
      });

      if (response.data) {
        setProgress(response.data);

        // Check if analysis completed or errored
        if (response.data.status === 'completed' || response.data.status === 'error') {
          if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
          }

          if (response.data.status === 'completed') {
            setMessage({
              type: 'success',
              text: `Analysis complete! Analyzed ${response.data.files_analyzed} files in ${formatTime(response.data.elapsed_seconds)}.`,
            });
            fetchStats(); // Refresh stats
          }

          // Clear localStorage
          localStorage.removeItem('codebase_progress_file');
          localStorage.removeItem('codebase_is_analyzing');

          setIsAnalyzing(false);
        }
      }
    } catch (error) {
      // Progress file might not exist yet, that's okay
      if (error.response?.status !== 404) {
        console.error('Error fetching progress:', error);
      }
    }
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!directory.trim()) {
      setMessage({ type: 'error', text: 'Please enter a directory path' });
      return;
    }

    setIsAnalyzing(true);
    setMessage(null);
    setAnalysisResult(null);
    setProgress(null);
    setProgressFile(null);

    try {
      const response = await axios.post('/analyze_codebase', {
        directory: directory,
        repo_name: repoName || null,
        github_url: githubUrl || null,
        pull_latest: pullLatest,
        is_private: isPrivate,
        privacy_password: privacyPassword,
      });

      if (response.data.success) {
        setAnalysisResult(response.data);
        setProgressFile(response.data.progress_file);

        // Save to localStorage for page refresh recovery
        localStorage.setItem('codebase_progress_file', response.data.progress_file);
        localStorage.setItem('codebase_is_analyzing', 'true');

        setMessage({
          type: 'info',
          text: 'Analysis started! Progress will update automatically...',
        });
      } else {
        const errorMsg = response.data.message || response.data.error || 'Analysis failed';
        const traceback = response.data.traceback;

        console.error('[CodebaseTab] Analysis failed:', errorMsg);
        if (traceback) {
          console.error('[CodebaseTab] Traceback:', traceback);
        }

        setMessage({
          type: 'error',
          text: `${errorMsg}${traceback ? '\n\nCheck browser console for full traceback.' : ''}`
        });
        setIsAnalyzing(false);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.response?.data?.error || 'Error analyzing codebase';
      const traceback = error.response?.data?.traceback;

      console.error('[CodebaseTab] Exception:', errorMsg);
      if (traceback) {
        console.error('[CodebaseTab] Full traceback:', traceback);
      }

      setMessage({
        type: 'error',
        text: `${errorMsg}${traceback ? '\n\nFull error in browser console (F12).' : ''}`,
      });
      setIsAnalyzing(false);
    }
  };

  const renderProgressBar = () => {
    if (!progress || !isAnalyzing) return null;

    const percent = progress.progress_percent || 0;
    const status = progress.status || 'initializing';
    const phase = progress.phase || 'initializing';

    return (
      <Box
        p={6}
        borderRadius="16px"
        bg={colorMode === 'dark' ? 'rgba(59, 130, 246, 0.08)' : 'rgba(59, 130, 246, 0.04)'}
        border="2px solid"
        borderColor={colorMode === 'dark' ? 'rgba(59, 130, 246, 0.3)' : 'rgba(59, 130, 246, 0.2)'}
        position="relative"
        overflow="hidden"
      >
        <VStack spacing={4} align="stretch">
          <HStack spacing={4} justify="space-between">
            <HStack spacing={3}>
              <CircularProgress
                value={percent}
                color="blue.400"
                size="60px"
                thickness="8px"
              >
                <CircularProgressLabel fontSize="sm" fontWeight="bold">
                  {percent}%
                </CircularProgressLabel>
              </CircularProgress>
              <Box>
                <Text fontSize="lg" fontWeight="700" color={colorMode === 'dark' ? 'white' : 'gray.900'}>
                  {status === 'processing' ? 'Analyzing Codebase' : 'Initializing...'}
                </Text>
                <Text fontSize="sm" color="gray.500">
                  Phase: {phase}
                </Text>
              </Box>
            </HStack>
            <Spinner size="md" color="blue.400" />
          </HStack>

          <Progress
            value={percent}
            size="lg"
            colorScheme="blue"
            borderRadius="full"
            hasStripe
            isAnimated
          />

          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <Stat>
              <StatLabel fontSize="xs" color="gray.500">Total Files</StatLabel>
              <StatNumber fontSize="xl" color="blue.400">
                {progress.total_files?.toLocaleString() || 0}
              </StatNumber>
            </Stat>

            <Stat>
              <StatLabel fontSize="xs" color="gray.500">Processed</StatLabel>
              <StatNumber fontSize="xl" color="green.400">
                {progress.files_processed?.toLocaleString() || 0}
              </StatNumber>
            </Stat>

            <Stat>
              <StatLabel fontSize="xs" color="gray.500">Rate</StatLabel>
              <StatNumber fontSize="xl" color="purple.400">
                {progress.processing_rate?.toFixed(1) || 0} <Text as="span" fontSize="sm">f/s</Text>
              </StatNumber>
            </Stat>

            <Stat>
              <StatLabel fontSize="xs" color="gray.500">ETA</StatLabel>
              <StatNumber fontSize="xl" color="orange.400">
                {progress.estimated_remaining_seconds > 0
                  ? formatTime(progress.estimated_remaining_seconds)
                  : '--'}
              </StatNumber>
            </Stat>
          </SimpleGrid>

          <Box
            p={3}
            borderRadius="8px"
            bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
          >
            <HStack spacing={2} mb={1}>
              <Icon as={FiFileText} color="blue.400" boxSize={4} />
              <Text fontSize="xs" fontWeight="600" color="gray.500">
                Current File:
              </Text>
            </HStack>
            <Text
              fontSize="sm"
              fontWeight="500"
              color={colorMode === 'dark' ? 'white' : 'gray.900'}
              isTruncated
            >
              {progress.current_file || 'Scanning...'}
            </Text>
          </Box>

          <HStack spacing={6} fontSize="xs" color="gray.500" justify="center">
            <HStack>
              <Icon as={FiClock} />
              <Text>Elapsed: {formatTime(progress.elapsed_seconds || 0)}</Text>
            </HStack>
            <Divider orientation="vertical" h="15px" />
            <HStack>
              <Text>✅ {progress.files_analyzed || 0}</Text>
              <Text>⏭️ {progress.files_skipped || 0}</Text>
              <Text>❌ {progress.files_errored || 0}</Text>
            </HStack>
          </HStack>
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
        transform: 'translateY(-2px)',
        borderColor: 'rgba(100,200,255,0.3)',
      }}
    >
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box
          p={6}
          borderRadius="16px"
          background={
            colorMode === 'dark'
              ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1))'
              : 'linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(5, 150, 105, 0.05))'
          }
          border="2px solid"
          borderColor={colorMode === 'dark' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(16, 185, 129, 0.2)'}
          position="relative"
          overflow="hidden"
          _before={{
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: 'linear-gradient(90deg, #10b981, #059669, #10b981)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 3s linear infinite',
          }}
        >
          <HStack spacing={3} align="center">
            <Icon as={AiOutlineCode} boxSize={8} color="#34d399" />
            <Box>
              <Text
                fontSize="2xl"
                fontWeight="700"
                color={colorMode === 'dark' ? 'white' : 'gray.900'}
                letterSpacing="-0.02em"
              >
                Analyze Codebase
              </Text>
              <Text fontSize="sm" color="gray.400" fontWeight="500">
                Extract metadata and store in Milvus for AI-powered code search
              </Text>
            </Box>
          </HStack>
        </Box>

        {/* Current Stats */}
        {stats && stats.analyzed && (
          <Box
            p={4}
            borderRadius="12px"
            bg={colorMode === 'dark' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.05)'}
            border="1px solid"
            borderColor={colorMode === 'dark' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(16, 185, 129, 0.15)'}
          >
            <HStack spacing={4}>
              <Icon as={FiFileText} color="green.400" boxSize={5} />
              <Box>
                <Text fontSize="sm" fontWeight="600" color={colorMode === 'dark' ? 'white' : 'gray.900'}>
                  Current Database
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {stats.total_entries} code entries indexed
                </Text>
              </Box>
            </HStack>
          </Box>
        )}

        {/* Progress Bar */}
        {renderProgressBar()}

        {/* Analysis Form */}
        <Box as="form" onSubmit={handleAnalyze}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel fontSize="sm" fontWeight="600">
                <HStack spacing={2}>
                  <Icon as={FiFolder} />
                  <Text>Directory Path</Text>
                </HStack>
              </FormLabel>
              <Input
                placeholder="/path/to/your/repository"
                value={directory}
                onChange={(e) => setDirectory(e.target.value)}
                size="md"
                borderRadius="12px"
                isDisabled={isAnalyzing}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                Absolute path to the codebase you want to analyze
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm" fontWeight="600">
                <HStack spacing={2}>
                  <Icon as={FiCode} />
                  <Text>Repository Name (Optional)</Text>
                </HStack>
              </FormLabel>
              <Input
                placeholder="my-awesome-project"
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                size="md"
                borderRadius="12px"
                isDisabled={isAnalyzing}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                Friendly name for this codebase (defaults to directory name)
              </Text>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm" fontWeight="600">
                <HStack spacing={2}>
                  <Icon as={FiGithub} />
                  <Text>GitHub URL (Optional)</Text>
                </HStack>
              </FormLabel>
              <Input
                placeholder="https://github.com/user/repository"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                size="md"
                borderRadius="12px"
                isDisabled={isAnalyzing}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                Link to GitHub repository for file URLs (auto-detected if git remote exists)
              </Text>
            </FormControl>

            <Box
              p={3}
              borderRadius="8px"
              bg={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.05)' : 'rgba(77, 124, 178, 0.02)'}
              borderBottom="3px solid"
              borderBottomColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.6)' : 'rgba(77, 124, 178, 0.4)'}
              boxShadow="sm"
            >
              <FormControl mb={2}>
                <Checkbox
                  isChecked={pullLatest}
                  onChange={(e) => setPullLatest(e.target.checked)}
                  isDisabled={isAnalyzing}
                  colorScheme="blue"
                  size="md"
                >
                  <HStack spacing={2}>
                    <Icon as={FiRefreshCw} boxSize={4} color="blue.500" />
                    <Text fontSize="sm" fontWeight="600" color={colorMode === 'dark' ? 'white' : 'gray.900'}>
                      Pull latest code from Git remote
                    </Text>
                  </HStack>
                </Checkbox>
                <Text fontSize="2xs" color="gray.500" mt={1} ml={5}>
                  Automatically runs 'git pull' before analysis (if Git repository)
                </Text>
              </FormControl>

              <Divider my={2} borderColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.2)' : 'rgba(77, 124, 178, 0.15)'} />

              <FormControl>
                <Checkbox
                  isChecked={isPrivate}
                  onChange={(e) => setIsPrivate(e.target.checked)}
                  isDisabled={isAnalyzing}
                  colorScheme="blue"
                  size="sm"
                >
                  <HStack spacing={2}>
                    <Text fontSize="xs" fontWeight="600" color={colorMode === 'dark' ? 'white' : 'gray.900'}>
                      🔒 Mark as Private
                    </Text>
                  </HStack>
                </Checkbox>
                <Text fontSize="2xs" color="gray.500" mt={1} ml={5}>
                  Private documents require password to access (default: public)
                </Text>
              </FormControl>

              {isPrivate && (
                <Box mt={2} ml={5}>
                  <FormControl>
                    <FormLabel fontSize="2xs" fontWeight="600" color="gray.500" mb={1}>
                      Privacy Password
                    </FormLabel>
                    <Input
                      type="password"
                      placeholder="Enter password (default: sdk)"
                      value={privacyPassword}
                      onChange={(e) => setPrivacyPassword(e.target.value)}
                      size="xs"
                      borderRadius="6px"
                      isDisabled={isAnalyzing}
                      borderColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.3)' : 'rgba(77, 124, 178, 0.2)'}
                      _focus={{
                        borderColor: 'blue.500',
                        boxShadow: '0 0 0 1px rgba(77, 124, 178, 0.6)',
                      }}
                    />
                    <Text fontSize="2xs" color="gray.500" mt={0.5}>
                      Case-insensitive. Default: "sdk"
                    </Text>
                  </FormControl>
                </Box>
              )}
            </Box>

            <Button
              type="submit"
              colorScheme="green"
              size="lg"
              leftIcon={isAnalyzing ? <Spinner size="sm" /> : <Icon as={AiOutlineCode} />}
              isLoading={isAnalyzing}
              loadingText="Analyzing..."
              borderRadius="12px"
              isDisabled={!directory.trim() || isAnalyzing}
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Codebase'}
            </Button>
          </VStack>
        </Box>

        {/* Messages */}
        {message && (
          <Alert
            status={message.type}
            borderRadius="12px"
            variant="left-accent"
          >
            <AlertIcon />
            <Box flex="1">
              <AlertDescription fontSize="sm" whiteSpace="pre-wrap">
                {message.text}
              </AlertDescription>
              {message.type === 'error' && (
                <Text fontSize="xs" color="red.600" mt={2}>
                  💡 Tip: Open browser console (F12) to see full error details
                </Text>
              )}
            </Box>
          </Alert>
        )}

        {/* Analysis Results */}
        {analysisResult && analysisResult.success && !isAnalyzing && (
          <Box
            p={6}
            borderRadius="16px"
            bg={colorMode === 'dark' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(16, 185, 129, 0.04)'}
            border="1px solid"
            borderColor={colorMode === 'dark' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(16, 185, 129, 0.15)'}
          >
            <VStack spacing={4} align="stretch">
              <HStack spacing={2}>
                <Icon as={FiCode} color="green.400" boxSize={5} />
                <Text fontSize="lg" fontWeight="700">
                  Analysis Complete ✅
                </Text>
              </HStack>

              <Divider />

              <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
                <Stat>
                  <StatLabel fontSize="xs" color="gray.500">
                    Files Analyzed
                  </StatLabel>
                  <StatNumber fontSize="2xl" color="green.400">
                    {analysisResult.files_analyzed}
                  </StatNumber>
                </Stat>

                <Stat>
                  <StatLabel fontSize="xs" color="gray.500">
                    Total Entries
                  </StatLabel>
                  <StatNumber fontSize="2xl" color="green.400">
                    {analysisResult.total_entries}
                  </StatNumber>
                  <StatHelpText fontSize="xs">Chunks in Milvus</StatHelpText>
                </Stat>

                <Stat>
                  <StatLabel fontSize="xs" color="gray.500">
                    Time Taken
                  </StatLabel>
                  <StatNumber fontSize="2xl" color="blue.400">
                    {formatTime(analysisResult.elapsed_seconds || 0)}
                  </StatNumber>
                </Stat>
              </SimpleGrid>

              <Box>
                <Text fontSize="sm" fontWeight="600" mb={2}>
                  Repository:
                </Text>
                <Code
                  p={2}
                  borderRadius="8px"
                  fontSize="sm"
                  bg={colorMode === 'dark' ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}
                >
                  {analysisResult.repo_name}
                </Code>
              </Box>
            </VStack>
          </Box>
        )}

        {/* Info Box */}
        <Box
          p={4}
          borderRadius="12px"
          bg={colorMode === 'dark' ? 'rgba(59, 130, 246, 0.05)' : 'rgba(59, 130, 246, 0.02)'}
          border="1px solid"
          borderColor={colorMode === 'dark' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(59, 130, 246, 0.1)'}
        >
          <VStack spacing={2} align="start">
            <HStack spacing={2}>
              <Icon as={FiSearch} color="blue.400" />
              <Text fontSize="sm" fontWeight="600" color={colorMode === 'dark' ? 'white' : 'gray.900'}>
                What Gets Analyzed:
              </Text>
            </HStack>
            <VStack align="start" spacing={1} fontSize="xs" color="gray.500" pl={6}>
              <Text>• Code structure: classes, functions, imports</Text>
              <Text>• Documentation: docstrings, comments</Text>
              <Text>• Metrics: lines of code, complexity scores</Text>
              <Text>• Relationships: dependencies between files</Text>
              <Text>• Semantic embeddings for AI-powered search</Text>
            </VStack>
          </VStack>
        </Box>

        {/* Supported Languages */}
        <Box
          p={4}
          borderRadius="12px"
          bg={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.05)' : 'rgba(77, 124, 178, 0.02)'}
          border="1px solid"
          borderColor={colorMode === 'dark' ? 'rgba(77, 124, 178, 0.15)' : 'rgba(77, 124, 178, 0.1)'}
        >
          <VStack spacing={2} align="start">
            <HStack spacing={2}>
              <Icon as={FiCode} color="blue.500" />
              <Text fontSize="sm" fontWeight="600" color={colorMode === 'dark' ? 'white' : 'gray.900'}>
                Supported Languages:
              </Text>
            </HStack>
            <HStack spacing={2} flexWrap="wrap" pl={6}>
              {[
                'Python',
                'JavaScript',
                'TypeScript',
                'Java',
                'Go',
                'Ruby',
                'PHP',
                'C/C++',
                'C#',
                'Swift',
                'Kotlin',
                'Rust',
                'Scala',
                'Shell',
                'SQL',
                'HTML/CSS',
              ].map((lang, idx) => (
                <Badge key={idx} variant="outline" colorScheme="blue" fontSize="2xs" px={2} py={0.5}>
                  {lang}
                </Badge>
              ))}
            </HStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
}

export default CodebaseTab;

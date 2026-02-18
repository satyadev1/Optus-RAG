import React, { useEffect } from 'react';
import {
  Box,
  Container,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  VStack,
  Icon,
  useColorMode,
  Flex,
  IconButton,
  Text,
} from '@chakra-ui/react';
import { FiUpload, FiSearch, FiGlobe, FiFileText, FiSun, FiMoon, FiMessageSquare, FiDatabase, FiBook, FiDollarSign, FiCode, FiImage } from 'react-icons/fi';
import { AiOutlineGithub } from 'react-icons/ai';
import { MdBugReport } from 'react-icons/md';
import { FaChartBar } from 'react-icons/fa';
import { SiConfluence } from 'react-icons/si';

import UploadTab from './components/UploadTab';
import JiraTab from './components/JiraTab';
import ConfluenceTab from './components/ConfluenceTab';
import GitHubTab from './components/GitHubTab';
import SearchTab from './components/SearchTab';
import CrawlerTab from './components/CrawlerTab';
import TextIndexTab from './components/TextIndexTab';
import RepoAnalyzerTab from './components/RepoAnalyzerTab';
import ChatInterface from './components/ChatInterface';
import ApiDocsTab from './components/ApiDocsTab';
import TokenUsageTab from './components/TokenUsageTab';
import CodebaseTab from './components/CodebaseTab';
import ImageManagerTab from './components/ImageManagerTab';
import LoadingModal from './components/LoadingModal';

function App() {
  const { colorMode, toggleColorMode } = useColorMode();
  const [isLoading, setIsLoading] = React.useState(true);

  // Set initial dark mode on mount
  useEffect(() => {
    setTimeout(() => {
      setIsLoading(false);
    }, 3500);
  }, []);

  return (
    <>
      <LoadingModal isOpen={isLoading} />
      <Box
        minH="100vh"
        bg={colorMode === 'dark'
          ? 'linear-gradient(135deg, #1e3a5f, #2c5f8d, #1a2332)'
          : 'linear-gradient(135deg, #e6f2ff, #cce5ff, #b3d9ff)'
        }
      >
      {/* Header - Compact Glassmorphism */}
      <Box
        backdropFilter="blur(20px)"
        background={colorMode === 'dark'
          ? "rgba(30,58,95,0.9)"
          : "rgba(255,255,255,0.9)"}
        borderBottom="1px solid"
        borderColor={colorMode === 'dark'
          ? "rgba(77,124,178,0.3)"
          : "rgba(77,124,178,0.2)"}
        boxShadow={colorMode === 'dark'
          ? "0 2px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(77,124,178,0.1)"
          : "0 2px 12px rgba(44,95,141,0.1), inset 0 1px 0 rgba(255,255,255,0.8)"}
        transition="all 300ms ease-in-out"
      >
        <Container maxW="container.xl">
          <Flex
            align="center"
            justify="center"
            py={2}
            px={3}
            position="relative"
          >
            {/* Theme Toggle - Positioned Absolute Right */}
            <IconButton
              aria-label="Toggle theme"
              icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
              onClick={toggleColorMode}
              backdropFilter="blur(12px)"
              background={colorMode === 'dark'
                ? "rgba(77,124,178,0.15)"
                : "rgba(77,124,178,0.1)"}
              border="1px solid"
              borderColor={colorMode === 'dark'
                ? "rgba(77,124,178,0.4)"
                : "rgba(77,124,178,0.3)"}
              color={colorMode === 'dark' ? "white" : "#1e3a5f"}
              _hover={{
                background: colorMode === 'dark'
                  ? "rgba(77,124,178,0.25)"
                  : "rgba(77,124,178,0.2)",
                transform: "translateY(-2px)",
                borderColor: colorMode === 'dark'
                  ? "rgba(77,124,178,0.6)"
                  : "rgba(77,124,178,0.5)",
              }}
              _active={{
                transform: "scale(0.95)",
              }}
              borderRadius="12px"
              size="md"
              transition="all 200ms ease-in-out"
              position="absolute"
              right={4}
            />

            {/* Logo and Text - Centered */}
            <Flex align="center" gap={3}>
              <Box
                p={2}
                borderRadius="12px"
                backdropFilter="blur(8px)"
                background="white"
                border="1px solid"
                borderColor={colorMode === 'dark'
                  ? "rgba(77,124,178,0.4)"
                  : "rgba(77,124,178,0.3)"}
                boxShadow={colorMode === 'dark'
                  ? "0 4px 16px rgba(44,95,141,0.2)"
                  : "0 4px 16px rgba(77,124,178,0.15)"}
                transition="all 200ms"
                _hover={{
                  transform: "scale(1.02)",
                  borderColor: colorMode === 'dark'
                    ? "rgba(77,124,178,0.6)"
                    : "rgba(77,124,178,0.5)",
                  boxShadow: colorMode === 'dark'
                    ? "0 6px 20px rgba(44,95,141,0.3)"
                    : "0 6px 20px rgba(77,124,178,0.25)",
                }}
              >
                <img
                  src="/logo.svg"
                  alt="RAG System"
                  style={{
                    width: '50px',
                    height: 'auto',
                    display: 'block'
                  }}
                />
              </Box>
              <VStack align="center" spacing={0}>
                <Text
                  fontSize="lg"
                  fontWeight="700"
                  letterSpacing="-0.02em"
                  color={colorMode === 'dark' ? "white" : "#1e293b"}
                  fontFamily="'Geist', 'Inter', sans-serif"
                >
                  RAG SYSTEM
                </Text>
                <Text
                  fontSize="2xs"
                  fontWeight="600"
                  color={colorMode === 'dark'
                    ? "rgba(179,217,255,0.9)"
                    : "rgba(77,124,178,0.8)"}
                  letterSpacing="wide"
                >
                  DATA INTELLIGENCE PLATFORM
                </Text>
              </VStack>
            </Flex>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="container.xl" py={8}>
        <Box
          backdropFilter="blur(16px)"
          background={colorMode === 'dark' ? "rgba(30,58,95,0.7)" : "rgba(255,255,255,0.85)"}
          rounded="20px"
          shadow="0 8px 32px rgba(30,58,95,0.2)"
          overflow="hidden"
          border="1px solid"
          borderColor={colorMode === 'dark' ? "rgba(77,124,178,0.3)" : "rgba(77,124,178,0.2)"}
          transition="all 300ms ease-in-out"
          animation="fadeInUp 350ms ease-in-out"
        >
          <Tabs colorScheme="blue" variant="soft-rounded">
            <TabList
              gap={3}
              p={4}
              sx={{
                '.chakra-tabs__tab': {
                  color: colorMode === 'dark' ? 'rgba(179,217,255,0.7)' : 'rgba(30,58,95,0.7)',
                  fontWeight: '600',
                  fontSize: 'md',
                  transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
                  borderRadius: '10px',
                  py: 3,
                  px: 5,
                  _selected: {
                    color: colorMode === 'dark' ? '#ffffff' : '#1e3a5f',
                    bg: colorMode === 'dark' ? 'rgba(77,124,178,0.9)' : 'rgba(230,242,255,1)',
                    boxShadow: colorMode === 'dark'
                      ? '0 2px 8px rgba(77,124,178,0.4)'
                      : '0 2px 12px rgba(77,124,178,0.25)',
                    border: '1px solid',
                    borderColor: colorMode === 'dark' ? 'rgba(77,124,178,0.5)' : 'rgba(77,124,178,0.4)',
                  },
                  _hover: {
                    color: colorMode === 'dark' ? 'rgba(255,255,255,0.9)' : '#2c5f8d',
                    bg: colorMode === 'dark' ? 'rgba(77,124,178,0.2)' : 'rgba(204,229,255,0.6)',
                  },
                },
              }}
            >
              <Tab>
                <Flex align="center" gap={2}>
                  <Icon as={FiMessageSquare} boxSize={5} />
                  <Text>AI Querying</Text>
                </Flex>
              </Tab>
              <Tab>
                <Flex align="center" gap={2}>
                  <Icon as={FiDatabase} boxSize={5} />
                  <Text>Data Retrieval</Text>
                </Flex>
              </Tab>
              <Tab>
                <Flex align="center" gap={2}>
                  <Icon as={FiDollarSign} boxSize={5} />
                  <Text>Token Usage</Text>
                </Flex>
              </Tab>
              <Tab>
                <Flex align="center" gap={2}>
                  <Icon as={FiBook} boxSize={5} />
                  <Text>API Docs</Text>
                </Flex>
              </Tab>
            </TabList>

            <TabPanels>
              <TabPanel p={0}>
                <ChatInterface />
              </TabPanel>
              <TabPanel p={6}>
                <Tabs colorScheme="blue" size="sm" variant="soft-rounded">
                  <TabList flexWrap="wrap" gap={2} mb={6}>
                    <Tab><Icon as={FiSearch} mr={2} />Search</Tab>
                    <Tab><Icon as={FiFileText} mr={2} />Index Text</Tab>
                    <Tab><Icon as={FiUpload} mr={2} />Upload File</Tab>
                    <Tab><Icon as={MdBugReport} mr={2} />Jira</Tab>
                    <Tab><Icon as={SiConfluence} mr={2} />Confluence</Tab>
                    <Tab><Icon as={AiOutlineGithub} mr={2} />GitHub</Tab>
                    <Tab><Icon as={FiGlobe} mr={2} />Crawler</Tab>
                    <Tab><Icon as={FaChartBar} mr={2} />PR Analyser</Tab>
                    <Tab><Icon as={FiCode} mr={2} />Codebase Analyser</Tab>
                    <Tab><Icon as={FiImage} mr={2} />Image Manager</Tab>
                  </TabList>

                  <TabPanels>
                    <TabPanel><SearchTab /></TabPanel>
                    <TabPanel><TextIndexTab /></TabPanel>
                    <TabPanel><UploadTab /></TabPanel>
                    <TabPanel><JiraTab /></TabPanel>
                    <TabPanel><ConfluenceTab /></TabPanel>
                    <TabPanel><GitHubTab /></TabPanel>
                    <TabPanel><CrawlerTab /></TabPanel>
                    <TabPanel><RepoAnalyzerTab /></TabPanel>
                    <TabPanel><CodebaseTab /></TabPanel>
                    <TabPanel><ImageManagerTab /></TabPanel>
                  </TabPanels>
                </Tabs>
              </TabPanel>
              <TabPanel p={6}>
                <TokenUsageTab />
              </TabPanel>
              <TabPanel p={6}>
                <ApiDocsTab />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      </Container>
    </Box>
    </>
  );
}

export default App;

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Textarea,
  Button,
  IconButton,
  Text,
  Flex,
  Select,
  Input,
  useColorMode,
  Divider,
  Badge,
  Avatar,
  Tooltip,
  Icon,
  Link,
  Wrap,
  WrapItem,
} from '@chakra-ui/react';
import { FiSend, FiPlus, FiTrash2, FiMessageSquare } from 'react-icons/fi';
import { GiBrain } from 'react-icons/gi';
import { AiOutlineRobot } from 'react-icons/ai';
import axios from 'axios';
import AnimatedSelect from './AnimatedSelect';

function ChatInterface() {
  const { colorMode } = useColorMode();

  // Load chats from localStorage on mount
  const [chats, setChats] = useState(() => {
    const savedChats = localStorage.getItem('optus_chat_history');
    return savedChats ? JSON.parse(savedChats) : [{ id: 1, name: 'New Chat', messages: [] }];
  });

  const [currentChatId, setCurrentChatId] = useState(() => {
    const savedCurrentId = localStorage.getItem('optus_current_chat_id');
    return savedCurrentId ? parseInt(savedCurrentId) : 1;
  });

  const [message, setMessage] = useState('');
  const [aiModel, setAiModel] = useState('claude');
  const [collection, setCollection] = useState('all');
  const [topK, setTopK] = useState(3);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Save chats to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('optus_chat_history', JSON.stringify(chats));
  }, [chats]);

  // Save current chat ID whenever it changes
  useEffect(() => {
    localStorage.setItem('optus_current_chat_id', currentChatId.toString());
  }, [currentChatId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chats]);

  const currentChat = chats.find(chat => chat.id === currentChatId);

  const createNewChat = () => {
    const newChatId = Math.max(...chats.map(c => c.id)) + 1;
    setChats([...chats, { id: newChatId, name: `Chat ${newChatId}`, messages: [] }]);
    setCurrentChatId(newChatId);
  };

  const deleteChat = (chatId) => {
    if (chats.length === 1) return;
    const updatedChats = chats.filter(c => c.id !== chatId);
    setChats(updatedChats);
    if (currentChatId === chatId) {
      setCurrentChatId(updatedChats[0].id);
    }
  };

  const clearAllChats = () => {
    const freshChats = [{ id: 1, name: 'New Chat', messages: [] }];
    setChats(freshChats);
    setCurrentChatId(1);
    localStorage.removeItem('optus_chat_history');
    localStorage.removeItem('optus_current_chat_id');
  };

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    // Update chat with user message
    const updatedChats = chats.map(chat => {
      if (chat.id === currentChatId) {
        return {
          ...chat,
          messages: [...chat.messages, userMessage],
          name: chat.messages.length === 0 ? message.slice(0, 30) + '...' : chat.name,
        };
      }
      return chat;
    });
    setChats(updatedChats);
    setMessage('');
    setIsLoading(true);

    try {
      const endpoint = aiModel === 'claude' ? '/ask_claude' : '/ask_ollama';
      const payload = {
        question: message,
        collection: collection,
        top_k: topK,
        context: currentChat.messages.map(m => ({ role: m.role, content: m.content })),
      };

      const response = await axios.post(endpoint, payload);

      if (response.data.success) {
        const aiMessage = {
          role: 'assistant',
          content: response.data.answer,
          model: response.data.model,
          sources: response.data.sources || [],
          confidence: response.data.confidence_score,
          timestamp: new Date().toISOString(),
        };

        setChats(prevChats => prevChats.map(chat => {
          if (chat.id === currentChatId) {
            return { ...chat, messages: [...chat.messages, aiMessage] };
          }
          return chat;
        }));
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: 'Error: Unable to get response from AI',
        timestamp: new Date().toISOString(),
      };
      setChats(prevChats => prevChats.map(chat => {
        if (chat.id === currentChatId) {
          return { ...chat, messages: [...chat.messages, errorMessage] };
        }
        return chat;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Flex h="calc(100vh - 200px)" overflow="hidden">
      {/* Sidebar - Chat History */}
      <Box
        w="200px"
        borderRight="1px solid"
        borderColor={colorMode === 'dark' ? 'rgba(77,124,178,0.3)' : 'rgba(77,124,178,0.2)'}
        p={2}
        overflowY="auto"
        bg={colorMode === 'dark' ? 'rgba(30,58,95,0.3)' : 'rgba(255,255,255,0.5)'}
      >
        <VStack spacing={1} mb={2}>
          <Button
            leftIcon={<FiPlus />}
            onClick={createNewChat}
            w="100%"
            colorScheme="blue"
            size="xs"
            borderRadius="8px"
            fontSize="xs"
          >
            New Chat
          </Button>
          {chats.length > 1 && (
            <Button
              leftIcon={<FiTrash2 />}
              onClick={clearAllChats}
              w="100%"
              colorScheme="red"
              variant="outline"
              size="xs"
              borderRadius="8px"
              fontSize="xs"
            >
              Clear All
            </Button>
          )}
        </VStack>

        <VStack spacing={1} align="stretch">
          {chats.map(chat => (
            <Flex
              key={chat.id}
              align="center"
              p={2}
              borderRadius="8px"
              cursor="pointer"
              bg={currentChatId === chat.id
                ? (colorMode === 'dark' ? 'rgba(77,124,178,0.3)' : 'rgba(77,124,178,0.2)')
                : 'transparent'
              }
              _hover={{
                bg: colorMode === 'dark' ? 'rgba(77,124,178,0.15)' : 'rgba(77,124,178,0.1)',
              }}
              onClick={() => setCurrentChatId(chat.id)}
              transition="all 200ms"
            >
              <Icon as={FiMessageSquare} mr={2} />
              <Text fontSize="sm" flex={1} isTruncated>
                {chat.name}
              </Text>
              {chats.length > 1 && (
                <IconButton
                  icon={<FiTrash2 />}
                  size="xs"
                  variant="ghost"
                  colorScheme="red"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteChat(chat.id);
                  }}
                />
              )}
            </Flex>
          ))}
        </VStack>
      </Box>

      {/* Main Chat Area */}
      <Flex flex={1} direction="column">
        {/* Settings Bar */}
        <Box
          p={4}
          borderBottom="1px solid"
          borderColor={colorMode === 'dark' ? 'rgba(77,124,178,0.3)' : 'rgba(77,124,178,0.2)'}
          bg={colorMode === 'dark' ? 'rgba(30,58,95,0.3)' : 'rgba(255,255,255,0.5)'}
        >
          <HStack spacing={4}>
            <Box w="180px">
              <AnimatedSelect
                value={aiModel}
                onChange={setAiModel}
                size="sm"
                placeholder="Select AI Model"
                options={[
                  { value: 'claude', label: '🧠 Claude AI' },
                  { value: 'ollama', label: '🤖 Ollama AI' },
                ]}
              />
            </Box>

            <Box w="240px">
              <AnimatedSelect
                value={collection}
                onChange={setCollection}
                size="sm"
                placeholder="Select Collection"
                options={[
                  { value: 'all', label: '🌟 All Collections' },
                  { value: 'jira_tickets', label: '📋 Jira Tickets' },
                  { value: 'github_prs', label: '🔀 GitHub PRs' },
                  { value: 'documents', label: '📄 Documents' },
                  { value: 'codebase_analysis', label: '💻 Codebase' },
                ]}
              />
            </Box>

            <Input
              type="number"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              min={1}
              max={10}
              w="100px"
              size="sm"
              placeholder="Top K"
            />
          </HStack>
        </Box>

        {/* Messages Area */}
        <Box
          flex={1}
          overflowY="auto"
          p={6}
          bg={colorMode === 'dark' ? 'rgba(0,0,0,0.1)' : 'rgba(248,250,252,0.5)'}
        >
          <VStack spacing={6} align="stretch">
            {currentChat?.messages.length === 0 ? (
              <VStack spacing={4} justify="center" h="100%" color="gray.500">
                <Icon as={aiModel === 'claude' ? GiBrain : AiOutlineRobot} boxSize={16} />
                <Text fontSize="xl" fontWeight="600">
                  Start a conversation
                </Text>
                <Text fontSize="sm">
                  Ask me anything about your data
                </Text>
              </VStack>
            ) : (
              currentChat?.messages.map((msg, idx) => (
                <Flex
                  key={idx}
                  gap={3}
                  align="start"
                  justify={msg.role === 'user' ? 'flex-end' : 'flex-start'}
                >
                  {msg.role === 'assistant' && (
                    <Avatar
                      icon={<Icon as={msg.model?.includes('claude') ? GiBrain : AiOutlineRobot} />}
                      size="sm"
                      bg="blue.600"
                    />
                  )}

                  <Box
                    maxW="70%"
                    p={4}
                    borderRadius="16px"
                    bg={msg.role === 'user'
                      ? (colorMode === 'dark' ? 'rgba(77,124,178,0.3)' : 'rgba(77,124,178,0.2)')
                      : (colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)')
                    }
                    border="1px solid"
                    borderColor={msg.role === 'user'
                      ? (colorMode === 'dark' ? 'rgba(77,124,178,0.4)' : 'rgba(77,124,178,0.3)')
                      : (colorMode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(100,116,139,0.2)')
                    }
                  >
                    <HStack spacing={2} mb={2} flexWrap="wrap">
                      {msg.model && (
                        <Badge colorScheme="blue" fontSize="xs">
                          {msg.model}
                        </Badge>
                      )}
                      {msg.confidence && (
                        <>
                          {/* Answer Confidence Badge */}
                          {msg.confidence.answer_confidence !== undefined && (
                            <Tooltip
                              label={`Answer Confidence: How certain Claude is about this answer. ${msg.confidence.level} (${(msg.confidence.answer_confidence * 100).toFixed(0)}%)`}
                              placement="top"
                            >
                              <Badge
                                variant="outline"
                                colorScheme={
                                  msg.confidence.answer_confidence >= 0.8 ? 'green' :
                                  msg.confidence.answer_confidence >= 0.65 ? 'blue' :
                                  msg.confidence.answer_confidence >= 0.5 ? 'yellow' :
                                  msg.confidence.answer_confidence >= 0.3 ? 'orange' : 'red'
                                }
                                fontSize="2xs"
                                cursor="help"
                                borderRadius="full"
                                px={2}
                                py={0.5}
                                fontWeight="600"
                              >
                                🎯 {(msg.confidence.answer_confidence * 100).toFixed(0)}%
                              </Badge>
                            </Tooltip>
                          )}

                          {/* Source Confidence Badge */}
                          {msg.confidence.source_confidence && (
                            <Tooltip
                              label={`Source Quality: Relevance of retrieved documents. Quality: ${msg.confidence.source_confidence.factors?.source_quality || 'N/A'} | Quantity: ${msg.confidence.source_confidence.factors?.source_quantity || 0} | Diversity: ${msg.confidence.source_confidence.factors?.source_diversity || 0} | High-Quality: ${msg.confidence.source_confidence.factors?.high_quality_sources || 0}`}
                              placement="top"
                            >
                              <Badge
                                variant="outline"
                                colorScheme={
                                  msg.confidence.source_confidence.score >= 0.8 ? 'green' :
                                  msg.confidence.source_confidence.score >= 0.65 ? 'blue' :
                                  msg.confidence.source_confidence.score >= 0.5 ? 'yellow' :
                                  msg.confidence.source_confidence.score >= 0.3 ? 'orange' : 'red'
                                }
                                fontSize="2xs"
                                cursor="help"
                                borderRadius="full"
                                px={2}
                                py={0.5}
                                fontWeight="600"
                              >
                                📚 {(msg.confidence.source_confidence.score * 100).toFixed(0)}%
                              </Badge>
                            </Tooltip>
                          )}

                          {/* Legacy: Single confidence (when only source available) */}
                          {msg.confidence.type === 'source_only' && msg.confidence.answer_confidence === undefined && (
                            <Tooltip
                              label={`Source Quality: ${msg.confidence.level} | Quality: ${msg.confidence.factors?.source_quality || 'N/A'} | Quantity: ${msg.confidence.factors?.source_quantity || 0} | Diversity: ${msg.confidence.factors?.source_diversity || 0} | High-Quality: ${msg.confidence.factors?.high_quality_sources || 0}`}
                              placement="top"
                            >
                              <Badge
                                variant="outline"
                                colorScheme={
                                  msg.confidence.score >= 0.8 ? 'green' :
                                  msg.confidence.score >= 0.65 ? 'blue' :
                                  msg.confidence.score >= 0.5 ? 'yellow' :
                                  msg.confidence.score >= 0.3 ? 'orange' : 'red'
                                }
                                fontSize="2xs"
                                cursor="help"
                                borderRadius="full"
                                px={2}
                                py={0.5}
                                fontWeight="600"
                              >
                                {(msg.confidence.score * 100).toFixed(0)}%
                              </Badge>
                            </Tooltip>
                          )}
                        </>
                      )}
                    </HStack>
                    <Text
                      whiteSpace="pre-wrap"
                      fontSize="sm"
                      lineHeight="tall"
                      color={colorMode === 'dark' ? 'white' : '#1e293b'}
                    >
                      {msg.content}
                    </Text>

                    {msg.sources && msg.sources.length > 0 && (
                      <Box mt={2} pt={2} borderTop="1px solid" borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}>
                        <Wrap spacing={2} align="center">
                          <WrapItem>
                            <Text fontSize="xs" fontWeight="600" color="gray.500">
                              Sources:
                            </Text>
                          </WrapItem>
                          {msg.sources.slice(0, 5).map((source, idx) => {
                            // Generate fallback title if missing or "Untitled"
                            let displayTitle = source.title;
                            if (!displayTitle || displayTitle.trim() === '' || displayTitle === 'Untitled') {
                              if (source.source_id) {
                                displayTitle = source.source_id;
                              } else if (source.collection) {
                                displayTitle = `${source.collection} document`;
                              } else if (source.source_type) {
                                displayTitle = `${source.source_type} item`;
                              } else {
                                displayTitle = `Source ${idx + 1}`;
                              }
                            }

                            return (
                              <WrapItem key={idx}>
                                <HStack spacing={1}>
                                  <Link
                                    href={source.url}
                                    isExternal
                                    fontSize="xs"
                                    color={colorMode === 'dark' ? 'cyan.300' : 'blue.500'}
                                    _hover={{ textDecoration: 'underline' }}
                                  >
                                    [{idx + 1}] {displayTitle}
                                  </Link>
                                  {source.score && (
                                    <Badge
                                      fontSize="2xs"
                                      colorScheme={source.score > 0.8 ? 'green' : source.score > 0.6 ? 'yellow' : 'orange'}
                                      px={1}
                                    >
                                      {(source.score * 100).toFixed(0)}%
                                    </Badge>
                                  )}
                                </HStack>
                              </WrapItem>
                            );
                          })}
                        </Wrap>
                      </Box>
                    )}
                  </Box>

                  {msg.role === 'user' && (
                    <Avatar size="sm" bg="blue.500" name="User" />
                  )}
                </Flex>
              ))
            )}
            {isLoading && (
              <Flex gap={3} align="start">
                <Avatar
                  icon={<Icon as={aiModel === 'claude' ? GiBrain : AiOutlineRobot} />}
                  size="sm"
                  bg="blue.600"
                />
                <Box
                  p={4}
                  borderRadius="16px"
                  bg={colorMode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.9)'}
                  border="1px solid"
                  borderColor={colorMode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(100,116,139,0.2)'}
                >
                  <HStack spacing={2}>
                    <Box w={2} h={2} borderRadius="full" bg="blue.600" animation="pulse 1s infinite" />
                    <Box w={2} h={2} borderRadius="full" bg="blue.600" animation="pulse 1s infinite 0.2s" />
                    <Box w={2} h={2} borderRadius="full" bg="blue.600" animation="pulse 1s infinite 0.4s" />
                  </HStack>
                </Box>
              </Flex>
            )}
            <div ref={messagesEndRef} />
          </VStack>
        </Box>

        {/* Input Area */}
        <Box
          p={4}
          borderTop="1px solid"
          borderColor={colorMode === 'dark' ? 'rgba(77,124,178,0.3)' : 'rgba(77,124,178,0.2)'}
          bg={colorMode === 'dark' ? 'rgba(30,58,95,0.3)' : 'rgba(255,255,255,0.5)'}
        >
          <HStack spacing={3}>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              rows={2}
              resize="none"
              borderRadius="16px"
            />
            <Tooltip label="Send message (Enter)">
              <IconButton
                icon={<FiSend />}
                onClick={handleSend}
                isLoading={isLoading}
                colorScheme="blue"
                size="lg"
                borderRadius="12px"
                isDisabled={!message.trim()}
              />
            </Tooltip>
          </HStack>
        </Box>
      </Flex>
    </Flex>
  );
}

export default ChatInterface;

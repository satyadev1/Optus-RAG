import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalBody,
  VStack,
  Text,
  Spinner,
  Box,
} from '@chakra-ui/react';

const LoadingModal = ({ isOpen }) => {
  const [greetingIndex, setGreetingIndex] = React.useState(0);
  const greetings = ['Hello', 'नमस्ते', 'Hola', 'Bonjour', '你好', 'こんにちは', 'Ciao'];

  React.useEffect(() => {
    if (isOpen) {
      const interval = setInterval(() => {
        setGreetingIndex((prev) => (prev + 1) % greetings.length);
      }, 300);
      return () => clearInterval(interval);
    }
  }, [isOpen, greetings.length]);

  return (
    <Modal isOpen={isOpen} isCentered closeOnOverlayClick={false}>
      <ModalOverlay
        bg="linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.98), rgba(49, 46, 129, 0.98))"
        backdropFilter="blur(24px)"
        animation="fadeIn 600ms ease-in-out"
      />
      <ModalContent
        backdropFilter="blur(20px)"
        background="linear-gradient(135deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98))"
        border="2px solid rgba(77,124,178,0.3)"
        borderRadius="24px"
        boxShadow="0 20px 60px rgba(77,124,178,0.4), inset 0 1px 0 rgba(255,255,255,0.5)"
        animation="macosHello 1.2s cubic-bezier(0.16, 1, 0.3, 1)"
        maxW="500px"
      >
        <ModalBody py={16}>
          <VStack spacing={8}>
            <Box
              animation="logoAppear 1s cubic-bezier(0.16, 1, 0.3, 1) 0.2s backwards"
              p={6}
              bg="white"
              borderRadius="20px"
              boxShadow="0 8px 32px rgba(77,124,178,0.2)"
            >
              <img
                src="/logo.svg"
                alt="RAG System"
                style={{
                  width: '280px',
                  height: 'auto',
                  display: 'block'
                }}
              />
            </Box>
            <Box
              animation="greetingFade 0.3s ease-in-out"
              key={greetingIndex}
            >
              <Text
                fontSize="4xl"
                fontWeight="600"
                color="#1e293b"
                letterSpacing="wider"
                textAlign="center"
                fontFamily="'Space Grotesk', sans-serif"
                textShadow="0 2px 4px rgba(0,0,0,0.1)"
              >
                {greetings[greetingIndex]}
              </Text>
            </Box>
            <Spinner
              size="xl"
              thickness="4px"
              speed="0.8s"
              color="#4d7cb2"
              emptyColor="rgba(77,124,178,0.2)"
              animation="spinnerFade 0.6s ease-in-out 0.8s backwards"
            />
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default LoadingModal;

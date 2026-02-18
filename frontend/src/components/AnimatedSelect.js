import React from 'react';
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
  Icon,
  useColorMode,
  Text,
  Box,
} from '@chakra-ui/react';
import { FiChevronDown, FiCheck } from 'react-icons/fi';

function AnimatedSelect({ value, onChange, options, placeholder = "Select option", size = "md" }) {
  const { colorMode } = useColorMode();

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <Menu matchWidth>
      {({ isOpen }) => (
        <>
          <MenuButton
            as={Button}
            rightIcon={
              <Icon
                as={FiChevronDown}
                transition="all 200ms"
                transform={isOpen ? 'rotate(180deg)' : 'rotate(0deg)'}
              />
            }
            w="100%"
            textAlign="left"
            fontWeight="500"
            fontSize={size === "sm" ? "sm" : "md"}
            h={size === "sm" ? "36px" : "44px"}
            backdropFilter="blur(12px)"
            background={colorMode === 'dark' ? 'rgba(100,200,255,0.1)' : 'rgba(255,255,255,0.9)'}
            border="1px solid"
            borderColor={colorMode === 'dark' ? 'rgba(100,200,255,0.35)' : 'rgba(100,116,139,0.2)'}
            color={colorMode === 'dark' ? '#ffffff' : '#1e293b'}
            _hover={{
              background: colorMode === 'dark' ? 'rgba(100,200,255,0.15)' : 'rgba(255,255,255,1)',
              borderColor: colorMode === 'dark' ? 'rgba(100,200,255,0.5)' : 'rgba(77,124,178,0.4)',
              boxShadow: colorMode === 'dark'
                ? '0 0 0 3px rgba(100,200,255,0.1)'
                : '0 0 0 3px rgba(77,124,178,0.08)',
              transform: 'translateY(-1px)',
            }}
            _active={{
              background: colorMode === 'dark' ? 'rgba(100,200,255,0.2)' : 'rgba(255,255,255,1)',
              borderColor: colorMode === 'dark' ? 'rgba(100,200,255,0.7)' : 'rgba(77,124,178,0.6)',
            }}
            transition="all 300ms cubic-bezier(0.4, 0, 0.2, 1)"
          >
            <Text isTruncated>
              {selectedOption ? selectedOption.label : placeholder}
            </Text>
          </MenuButton>
          <MenuList
            backdropFilter="blur(16px)"
            background={colorMode === 'dark' ? 'rgba(30, 41, 59, 0.95)' : 'rgba(255, 255, 255, 0.95)'}
            border="1px solid"
            borderColor={colorMode === 'dark' ? 'rgba(100,200,255,0.3)' : 'rgba(100,116,139,0.2)'}
            borderRadius="12px"
            boxShadow={colorMode === 'dark'
              ? '0 10px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(100,200,255,0.2)'
              : '0 10px 40px rgba(0,0,0,0.15), 0 0 0 1px rgba(100,116,139,0.1)'
            }
            py={2}
            maxH="300px"
            overflowY="auto"
            zIndex={1500}
            animation="dropdownSlideIn 200ms cubic-bezier(0.4, 0, 0.2, 1)"
            sx={{
              '@keyframes dropdownSlideIn': {
                from: {
                  opacity: 0,
                  transform: 'translateY(-10px) scale(0.95)',
                },
                to: {
                  opacity: 1,
                  transform: 'translateY(0) scale(1)',
                },
              },
            }}
          >
            {options.map((option, index) => (
              <MenuItem
                key={option.value}
                onClick={() => onChange(option.value)}
                background="transparent"
                color={colorMode === 'dark' ? '#ffffff' : '#1e293b'}
                fontSize={size === "sm" ? "sm" : "md"}
                px={4}
                py={3}
                fontWeight={value === option.value ? '600' : '500'}
                borderBottom={index < options.length - 1 ? '1px solid' : 'none'}
                borderColor={colorMode === 'dark' ? 'rgba(100,200,255,0.1)' : 'rgba(100,116,139,0.1)'}
                _hover={{
                  background: colorMode === 'dark'
                    ? 'linear-gradient(90deg, rgba(100,200,255,0.3), rgba(100,200,255,0.2))'
                    : 'linear-gradient(90deg, rgba(77,124,178,0.15), rgba(77,124,178,0.08))',
                  paddingLeft: '20px',
                }}
                _focus={{
                  background: colorMode === 'dark'
                    ? 'rgba(100,200,255,0.25)'
                    : 'rgba(77,124,178,0.12)',
                }}
                transition="all 200ms ease"
                position="relative"
              >
                <Box display="flex" alignItems="center" justifyContent="space-between" w="100%">
                  <Text>{option.label}</Text>
                  {value === option.value && (
                    <Icon
                      as={FiCheck}
                      color={colorMode === 'dark' ? 'rgba(100,200,255,1)' : '#4338ca'}
                      boxSize={4}
                      ml={2}
                    />
                  )}
                </Box>
              </MenuItem>
            ))}
          </MenuList>
        </>
      )}
    </Menu>
  );
}

export default AnimatedSelect;

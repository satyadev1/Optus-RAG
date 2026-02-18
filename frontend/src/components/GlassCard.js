import React from 'react';
import { Box } from '@chakra-ui/react';

const GlassCard = ({ children, hoverScale = true, ...props }) => {
  return (
    <Box
      backdropFilter="blur(8px)"
      background="rgba(100,200,255,0.08)"
      border="1px solid rgba(255,255,255,0.15)"
      borderRadius="20px"
      boxShadow="0 8px 32px rgba(0,0,0,0.25)"
      p={6}
      transition="all 300ms ease-in-out"
      _hover={
        hoverScale
          ? {
              transform: 'scale(1.02)',
              boxShadow: '0 12px 40px rgba(0,0,0,0.35)',
              borderColor: 'rgba(255,255,255,0.25)',
            }
          : {}
      }
      {...props}
    >
      {children}
    </Box>
  );
};

export default GlassCard;

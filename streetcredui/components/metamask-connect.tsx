"use client"

import React, { useEffect } from 'react';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { Button } from '@/components/ui/button';
import { metaMask } from 'wagmi/connectors';

export interface MetaMaskConnectProps {
  children: React.ReactNode
  className?: string
  onConnect?: () => void
}

export default function MetaMaskConnect({ children, className, onConnect }: MetaMaskConnectProps) {
  const { address, isConnected } = useAccount();
  const { connect } = useConnect();
  const { disconnect } = useDisconnect();

  // Log connection data whenever it changes
  useEffect(() => {
    if (isConnected && address) {
      console.log({
        walletAddress: address,
        connectionData: {
          address,
          network: 'Flare Coston2',
          timestamp: new Date().toISOString(),
        }
      });
    }
  }, [isConnected, address]);

  const handleConnect = async () => {
    try {
      await connect({ connector: metaMask() });
      onConnect?.();
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  };

  if (isConnected) {
    return (
      <Button 
        onClick={() => disconnect()} 
        className={className}
      >
        {children}
      </Button>
    );
  }

  return (
    <Button 
      onClick={handleConnect} 
      className={className}
    >
      {children}
    </Button>
  );
} 
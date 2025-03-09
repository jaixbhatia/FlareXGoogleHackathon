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

      // Create async function and call it immediately
      /*const fetchData = async () => {
        const exchangeResponse = await fetch(`http://localhost:8080/api/routes/plaid/set_wallet_address`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({ address }),
          credentials: 'include',
        });
        
        if (!exchangeResponse.ok) {
          const errorData = await exchangeResponse.text();
          console.error('Error exchanging public token:', errorData);
          return;
        }
      };
      
      fetchData().catch(console.error);*/
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
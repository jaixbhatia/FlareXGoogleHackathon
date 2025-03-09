"use client"

import React, { useCallback, useEffect } from 'react';
import { usePlaidLink } from 'react-plaid-link';
import { usePlaid } from '@/lib/plaid';
import { Button } from '@/components/ui/button';

interface PlaidLinkProps {
  className?: string;
  children?: React.ReactNode;
}

const PlaidLink: React.FC<PlaidLinkProps> = ({ className, children }) => {
  const { state: { linkToken, isPaymentInitiation }, dispatch } = usePlaid();

  const onSuccess = useCallback(
    async (public_token: string) => {
      try {
        // Exchange public token for access token using our TEE backend
        const exchangeResponse = await fetch('http://localhost:8000/plaid/exchange_public_token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ public_token }),
        });
        
        if (!exchangeResponse.ok) {
          console.error('Error exchanging public token');
          return;
        }

        const data = await exchangeResponse.json();

        // Update UI state
        dispatch({
          type: 'SET_STATE',
          state: {
            itemId: data.item_id,
            accessToken: data.access_token,
            isItemAccess: true,
            linkSuccess: true,
          },
        });

        if (isPaymentInitiation) {
          // Additional payment initiation logic if needed
        }
      } catch (error) {
        console.error('Error in Plaid flow:', error);
      }
    },
    [dispatch, isPaymentInitiation]
  );

  const config: Parameters<typeof usePlaidLink>[0] = {
    token: linkToken!,
    onSuccess,
  };

  const { open, ready } = usePlaidLink(config);

  useEffect(() => {
    if (linkToken == null) {
      const getInfo = async () => {
        const response = await fetch('/api/plaid/info', { method: 'POST' });
        if (!response.ok) {
          dispatch({ type: 'SET_STATE', state: { backend: false } });
          return;
        }
        const data = await response.json();
        dispatch({
          type: 'SET_STATE',
          state: {
            products: data.products,
            isPaymentInitiation: data.products.includes('payment_initiation'),
          },
        });
      };
      getInfo();

      const generateToken = async () => {
        const path = isPaymentInitiation
          ? '/api/plaid/create_link_token_for_payment'
          : '/api/plaid/create_link_token';
        const response = await fetch(path, {
          method: 'POST',
        });
        if (!response.ok) {
          dispatch({ type: 'SET_STATE', state: { linkToken: null } });
          return;
        }
        const data = await response.json();
        if (data) {
          if (data.error != null) {
            dispatch({
              type: 'SET_STATE',
              state: {
                linkToken: null,
                linkTokenError: data.error,
              },
            });
            return;
          }
          dispatch({ type: 'SET_STATE', state: { linkToken: data.link_token } });
        }
        localStorage.setItem('link_token', data.link_token); // Save for OAuth
      };
      generateToken();
    }
  }, [dispatch, linkToken, isPaymentInitiation]);

  return (
    <Button
      onClick={() => open()}
      disabled={!ready || !linkToken}
      className={className}
      variant="default"
    >
      {children || 'Link Bank Account'}
    </Button>
  );
};

export default PlaidLink; 
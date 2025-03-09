"use client"

import React, { useCallback, useEffect } from 'react';
import { usePlaidLink } from 'react-plaid-link';
import { usePlaid } from '@/lib/plaid';
import { Button } from '@/components/ui/button';

interface PlaidLinkProps {
  className?: string;
  children?: React.ReactNode;
}

const BACKEND_URL = 'http://localhost:8080';
const API_PREFIX = '/api/routes/plaid';

const PlaidLink: React.FC<PlaidLinkProps> = ({ className, children }) => {
  const { state: { linkToken, isPaymentInitiation }, dispatch } = usePlaid();

  const onSuccess = useCallback(
    async (public_token: string) => {
      try {
        console.log(public_token)
        // Exchange public token for access token using our TEE backend
        const exchangeResponse = await fetch(`${BACKEND_URL}${API_PREFIX}/set_access_token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({ public_token }),
          credentials: 'include',
        });
        
        if (!exchangeResponse.ok) {
          const errorData = await exchangeResponse.text();
          console.error('Error exchanging public token:', errorData);
          return;
        }

        const data = await exchangeResponse.json();

        // Quick validation check with the backend
        const validationResponse = await fetch(`${BACKEND_URL}${API_PREFIX}/info`, {
          headers: {
            'Accept': 'application/json',
          },
          credentials: 'include',
        });
        const validationData = await validationResponse.json();
        
        if (validationData.access_token) {
          console.log('✅ Backend successfully received Plaid token');
        } else {
          console.error('❌ Backend did not receive Plaid token');
        }

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
        const response = await fetch(`${BACKEND_URL}${API_PREFIX}/info`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          credentials: 'include',
        });
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
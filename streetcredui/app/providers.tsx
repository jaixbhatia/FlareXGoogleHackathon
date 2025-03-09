"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, WagmiProvider, createConfig } from "wagmi";
import { metaMask } from "wagmi/connectors";

// Define Flare Coston2 testnet
const coston2 = {
  id: 114,
  name: 'Coston2',
  nativeCurrency: {
    decimals: 18,
    name: 'Coston2',
    symbol: 'C2FLR',
  },
  rpcUrls: {
    default: { 
      http: [process.env.NEXT_PUBLIC_FLARE_RPC_URL || 'https://coston2-api.flare.network/ext/C/rpc'],
    },
    public: {
      http: [process.env.NEXT_PUBLIC_FLARE_RPC_URL || 'https://coston2-api.flare.network/ext/C/rpc'],
    },
  },
  blockExplorers: {
    default: {
      name: 'Coston2 Explorer',
      url: 'https://coston2-explorer.flare.network',
    },
  },
  testnet: true,
} as const;

const config = createConfig({
  chains: [coston2],
  connectors: [metaMask()],
  transports: {
    [coston2.id]: http(),
  },
});

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </WagmiProvider>
  );
} 
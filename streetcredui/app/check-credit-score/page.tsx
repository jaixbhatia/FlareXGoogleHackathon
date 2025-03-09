"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { NavBar } from "@/components/nav-bar"
import { ArrowRight, BanknoteIcon as Bank, Check, Wallet } from "lucide-react"
import { CreditScoreDisplay } from "@/components/credit-score-display"
import PlaidLink from "@/components/plaid-link"
import MetaMaskConnect from "@/components/metamask-connect"
import { usePlaid } from "@/lib/plaid"

export default function CheckCreditScore() {
  const [walletConnected, setWalletConnected] = useState(false)
  const [scoreChecked, setScoreChecked] = useState(false)
  const { state: { linkSuccess: bankConnected } } = usePlaid()

  const handleCheckScore = () => {
    // In a real app, this would fetch the credit score
    setTimeout(() => {
      setScoreChecked(true)
    }, 2000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f5f5f5] to-white text-white">
      <NavBar />
      
      <div className="container mx-auto px-4 pt-24 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-[#363636]">Check Your Credit Score</h1>
          <p className="text-xl text-[#363636]/80">
            Connect your bank account and crypto wallet to get a comprehensive credit score that reflects your complete
            financial picture.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {!scoreChecked ? (
            <motion.div
              key="connect-steps"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto"
            >
              <Card className="bg-[#f5f5f5]/80 border-[#363636]/10">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Bank className="mr-2 h-6 w-6 text-[#e72c61]" />
                    Connect Your Bank
                  </CardTitle>
                  <CardDescription>
                    Securely connect your bank accounts through Plaid to analyze your traditional financial data.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-40 flex items-center justify-center">
                    {bankConnected ? (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="bg-green-500/20 rounded-full p-4"
                      >
                        <Check className="h-12 w-12 text-[#e72c61]" />
                      </motion.div>
                    ) : (
                      <Bank className="h-16 w-16 text-gray-400" />
                    )}
                  </div>
                </CardContent>
                <CardFooter>
                  <PlaidLink className="w-full bg-[#e72c61] hover:bg-[#e72c61]">
                    {bankConnected ? "Connected" : "Connect Bank"}
                  </PlaidLink>
                </CardFooter>
              </Card>

              <Card className="bg-[#f5f5f5]/80 border-[#363636]/10">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Wallet className="mr-2 h-6 w-6 text-[#e72c61]" />
                    Connect Your Wallet
                  </CardTitle>
                  <CardDescription>
                    Link your crypto wallet to analyze your on-chain activity and transactions.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-40 flex items-center justify-center">
                    {walletConnected ? (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="bg-green-500/20 rounded-full p-4"
                      >
                        <Check className="h-12 w-12 text-[#e72c61]" />
                      </motion.div>
                    ) : (
                      <Wallet className="h-16 w-16 text-gray-400" />
                    )}
                  </div>
                </CardContent>
                <CardFooter>
                  <MetaMaskConnect 
                    className="w-full bg-[#e72c61] hover:bg-[#e72c61]"
                    onConnect={() => setWalletConnected(true)}
                  >
                    {walletConnected ? "Connected" : "Connect Wallet"}
                  </MetaMaskConnect>
                </CardFooter>
              </Card>

              <div className="md:col-span-2 mt-8">
                <Button
                  size="lg"
                  className="w-full bg-[#e72c61] hover:bg-[#e72c61] py-8 text-xl"
                  disabled={!bankConnected || !walletConnected}
                  onClick={handleCheckScore}
                >
                  Check Your Credit Score
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="score-display"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <CreditScoreDisplay />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}


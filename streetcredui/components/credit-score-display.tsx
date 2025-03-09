"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowUpRight, Download, Info, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"

export function CreditScoreDisplay() {
  const [score, setScore] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      // Simulate score calculation
      const finalScore = 742
      let currentScore = 0
      const interval = setInterval(() => {
        currentScore += 10
        setScore(currentScore)
        setProgress((currentScore / 850) * 100)

        if (currentScore >= finalScore) {
          clearInterval(interval)
          setScore(finalScore)
          setProgress((finalScore / 850) * 100)
        }
      }, 30)

      return () => clearInterval(interval)
    }, 500)

    return () => clearTimeout(timer)
  }, [])

  const getScoreColor = () => {
    if (score < 580) return "text-red-500"
    if (score < 670) return "text-yellow-500"
    if (score < 740) return "text-blue-500"
    return "text-[#e72c61]"
  }

  const getScoreCategory = () => {
    if (score < 580) return "Poor"
    if (score < 670) return "Fair"
    if (score < 740) return "Good"
    return "Excellent"
  }

  const getProgressColor = () => {
    if (score < 580) return "bg-red-500"
    if (score < 670) return "bg-yellow-500"
    if (score < 740) return "bg-blue-500"
    return "bg-[#e72c61]"
  }

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-8"
      >
        <h2 className="text-3xl font-bold text-black mb-2">Your StreetCred Score</h2>
        <p className="text-[#363636]/70">Based on your traditional and on-chain financial activity</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card className="bg-[#f5f5f5]/80 border-[#363636]/10 h-full">
            <CardHeader>
              <CardTitle>Credit Score</CardTitle>
              <CardDescription>Your comprehensive credit score based on all financial data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-8">
                <div className="relative mb-6">
                  <motion.div
                    className={`text-7xl font-bold ${getScoreColor()}`}
                    initial={{ scale: 0.5 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.5, type: "spring" }}
                  >
                    {score}
                  </motion.div>
                  <motion.div
                    className="absolute -top-2 -right-8 bg-green-500/20 text-[#e72c61] px-2 py-1 rounded-md text-sm font-medium flex items-center"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 1.5 }}
                  >
                    <TrendingUp className="h-3 w-3 mr-1" />
                    +15
                  </motion.div>
                </div>

                <motion.div
                  className="text-xl font-medium mb-6"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.5, delay: 0.8 }}
                >
                  {getScoreCategory()} Credit
                </motion.div>

                <div className="w-full max-w-md mb-4">
                  <div className="flex justify-between mb-2 text-sm">
                    <span>Poor</span>
                    <span>Fair</span>
                    <span>Good</span>
                    <span>Excellent</span>
                  </div>
                  <div className="h-2 w-full bg-[#363636]/20 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${getProgressColor()}`}
                      initial={{ width: "0%" }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 1, delay: 0.5 }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 w-full max-w-md mt-8">
                  <Button variant="outline" className="border-[#363636]/10">
                    <Download className="h-4 w-4 mr-2" />
                    Download Report
                  </Button>
                  <Button className="bg-[#e72c61] hover:bg-[#e72c61]">
                    <Info className="h-4 w-4 mr-2" />
                    Score Details
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Card className="bg-[#f5f5f5]/80 border-[#363636]/10 h-full">
            <CardHeader>
              <CardTitle>Score Breakdown</CardTitle>
              <CardDescription>What contributes to your score</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="factors">
                <TabsList className="grid w-full grid-cols-2 mb-4">
                  <TabsTrigger value="factors">Factors</TabsTrigger>
                  <TabsTrigger value="history">History</TabsTrigger>
                </TabsList>

                <TabsContent value="factors" className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Payment History</span>
                      <span className="text-sm font-medium text-[#e72c61]">Excellent</span>
                    </div>
                    <Progress value={95} className="h-2 bg-[#363636]/20" indicatorClassName="bg-[#e72c61]" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Credit Utilization</span>
                      <span className="text-sm font-medium text-blue-500">Good</span>
                    </div>
                    <Progress value={75} className="h-2 bg-[#363636]/20" indicatorClassName="bg-blue-500" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">On-Chain Activity</span>
                      <span className="text-sm font-medium text-[#e72c61]">Excellent</span>
                    </div>
                    <Progress value={90} className="h-2 bg-[#363636]/20" indicatorClassName="bg-[#e72c61]" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Credit Age</span>
                      <span className="text-sm font-medium text-yellow-500">Fair</span>
                    </div>
                    <Progress value={60} className="h-2 bg-[#363636]/20" indicatorClassName="bg-yellow-500" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">New Credit</span>
                      <span className="text-sm font-medium text-blue-500">Good</span>
                    </div>
                    <Progress value={80} className="h-2 bg-[#363636]/20" indicatorClassName="bg-blue-500" />
                  </div>
                </TabsContent>

                <TabsContent value="history">
                  <div className="space-y-4">
                    {[
                      { date: "Mar 2025", score: 742, change: "+15" },
                      { date: "Feb 2025", score: 727, change: "+8" },
                      { date: "Jan 2025", score: 719, change: "+12" },
                      { date: "Dec 2024", score: 707, change: "+5" },
                      { date: "Nov 2024", score: 702, change: "+10" },
                    ].map((item, index) => (
                      <div key={index} className="flex justify-between items-center border-b border-[#363636]/10 pb-2">
                        <span>{item.date}</span>
                        <div className="flex items-center">
                          <span className="font-medium mr-2">{item.score}</span>
                          <span className="text-[#e72c61] text-sm flex items-center">
                            {item.change}
                            <ArrowUpRight className="h-3 w-3 ml-1" />
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        <Card className="bg-[#f5f5f5]/80 border-[#363636]/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li className="flex items-start">
                <div className="bg-green-500/20 rounded-full p-1 mr-2 mt-0.5">
                  <Check className="h-3 w-3 text-[#e72c61]" />
                </div>
                <span className="text-sm">Maintain low credit utilization</span>
              </li>
              <li className="flex items-start">
                <div className="bg-green-500/20 rounded-full p-1 mr-2 mt-0.5">
                  <Check className="h-3 w-3 text-[#e72c61]" />
                </div>
                <span className="text-sm">Continue on-time payments</span>
              </li>
              <li className="flex items-start">
                <div className="bg-yellow-500/20 rounded-full p-1 mr-2 mt-0.5">
                  <Info className="h-3 w-3 text-yellow-500" />
                </div>
                <span className="text-sm">Consider diversifying credit mix</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card className="bg-[#f5f5f5]/80 border-[#363636]/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Loan Eligibility</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Personal Loan</span>
                <span className="text-[#e72c61] font-medium text-sm">Excellent</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Mortgage</span>
                <span className="text-[#e72c61] font-medium text-sm">Excellent</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Auto Loan</span>
                <span className="text-[#e72c61] font-medium text-sm">Excellent</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">DeFi Lending</span>
                <span className="text-blue-500 font-medium text-sm">Good</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#f5f5f5]/80 border-[#363636]/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">On-Chain Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Transaction History</span>
                <span className="text-[#e72c61] font-medium text-sm">Strong</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Wallet Age</span>
                <span className="text-blue-500 font-medium text-sm">Good</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">DeFi Participation</span>
                <span className="text-[#e72c61] font-medium text-sm">Active</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">NFT Activity</span>
                <span className="text-yellow-500 font-medium text-sm">Moderate</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

function Check(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}


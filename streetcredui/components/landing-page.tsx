"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, CheckCircle, Code, CreditCard, Database, Lock, Shield } from "lucide-react"
import { NavBar } from "@/components/nav-bar"
import { CanvasRevealEffect } from "@/components/ui/canvas-reveal-effect"
import Image from "next/image"

export default function LandingPage() {
  const [isHovered, setIsHovered] = useState(false)

  const benefits = [
    {
      icon: <Database className="h-8 w-8 text-[#e72c61]" />,
      title: "Comprehensive Data",
      description: "Combine traditional and on-chain data for a complete credit picture",
    },
    {
      icon: <Shield className="h-8 w-8 text-[#e72c61]" />,
      title: "Secure & Private",
      description: "Bank-level encryption and privacy-preserving technology",
    },
    {
      icon: <Lock className="h-8 w-8 text-[#e72c61]" />,
      title: "User Controlled",
      description: "Users own their data and control who can access it",
    },
    {
      icon: <Code className="h-8 w-8 text-[#e72c61]" />,
      title: "Developer Friendly",
      description: "Easy to integrate API with comprehensive documentation",
    },
  ]

  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      <NavBar />

      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <CanvasRevealEffect
            animationSpeed={2}
            containerClassName="bg-[#f5f5f5]"
            colors={[
              [231, 44, 97], // #e72c61
              [194, 15, 69], // #c20f45
            ]}
          />
        </div>

        <div className="container relative z-10 mx-auto px-4 text-center">
          <motion.h1
            className="text-5xl md:text-7xl font-bold mb-6 text-[#363636]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            The Future of Credit is On-Chain
          </motion.h1>

          <motion.p
            className="text-xl md:text-2xl mb-10 max-w-3xl mx-auto text-[#363636]/80"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            StreetCred combines traditional financial data with on-chain activity to create the most accurate credit
            scoring system for the digital age.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Link href="/check-credit-score">
              <Button
                size="lg"
                className="px-8 py-6 text-lg rounded-xl w-full sm:w-auto"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
              >
                Check Your Credit Score
                <motion.span animate={{ x: isHovered ? 5 : 0 }} transition={{ duration: 0.2 }}>
                  <ArrowRight className="ml-2 h-5 w-5" />
                </motion.span>
              </Button>
            </Link>

            <Link href="/develop-with-us">
              <Button size="lg" variant="outline" className="px-8 py-6 text-lg rounded-xl w-full sm:w-auto">
                Develop With Us
              </Button>
            </Link>
          </motion.div>
        </div>

        <motion.div
          className="absolute bottom-10 left-0 right-0 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
        >
          <p className="text-[#363636]/70">Scroll to learn more</p>
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY }}
            className="mt-2"
          >
            ↓
          </motion.div>
        </motion.div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-[#363636]">Why Choose StreetCred</h2>
            <p className="text-xl text-[#363636]/80 max-w-3xl mx-auto">
              Our platform offers unique advantages for both consumers and businesses.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((benefit, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="bg-[#f5f5f5] p-8 rounded-2xl border border-[#e72c61]/10 hover:border-[#e72c61]/50 transition-all duration-300"
              >
                <div className="mb-4">{benefit.icon}</div>
                <h3 className="text-xl font-bold mb-2 text-[#363636]">{benefit.title}</h3>
                <p className="text-[#363636]/80">{benefit.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="lg:w-1/2"
            >
              <h2 className="text-3xl md:text-4xl font-bold mb-6 text-[#363636]">Our Mission</h2>
              <p className="text-xl text-[#363636]/80 mb-6">
                At StreetCred, we believe that credit scoring should evolve with the changing financial landscape.
                Traditional credit systems often fail to capture the full financial picture of individuals in the
                digital economy.
              </p>
              <p className="text-xl text-[#363636]/80 mb-6">
                We're building a bridge between traditional finance and the blockchain world, creating a more inclusive,
                accurate, and user-controlled credit system for the future.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-[#e72c61] mr-2" />
                  <span>Financial Inclusion</span>
                </div>
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-[#e72c61] mr-2" />
                  <span>Data Ownership</span>
                </div>
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-[#e72c61] mr-2" />
                  <span>Transparent Scoring</span>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="lg:w-1/2 relative h-[400px] w-full"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-[#e72c61]/20 to-[#c20f45]/20 rounded-2xl overflow-hidden">
                <div className="h-full w-full flex items-center justify-center">
                  <CreditCard className="h-32 w-32 text-[#e72c61] opacity-50" />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-6 text-[#363636]">Ready to Get Started?</h2>
            <p className="text-xl text-[#363636]/80 mb-10">
              Whether you're looking to check your credit score or integrate our API into your lending platform,
              StreetCred has you covered.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/check-credit-score">
                <Button size="lg" className="w-full sm:w-auto">
                  Check Your Credit Score
                </Button>
              </Link>

              <Link href="/develop-with-us">
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  Develop With Us
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-[#363636]/10">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-6 md:mb-0">
              <Link href="/" className="flex items-center space-x-2">
                <Image
                  src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/slogo-K0TLgY8fPdGH0RAZiiT1awcD8quZVW.png"
                  alt="streetcred logo"
                  width={20}
                  height={20}
                  className="h-5 w-5"
                />
                <span className="text-lg font-normal text-[#e72c61]">streetcred</span>
              </Link>
              <p className="text-[#363636]/70 mt-2">The Future of Credit is On-Chain</p>
            </div>

            <div className="flex gap-8">
              <Link href="/about" className="text-[#363636]/70 hover:text-[#e72c61] transition-colors">
                About
              </Link>
              <Link href="/privacy" className="text-[#363636]/70 hover:text-[#e72c61] transition-colors">
                Privacy
              </Link>
              <Link href="/terms" className="text-[#363636]/70 hover:text-[#e72c61] transition-colors">
                Terms
              </Link>
              <Link href="/contact" className="text-[#363636]/70 hover:text-[#e72c61] transition-colors">
                Contact
              </Link>
            </div>
          </div>

          <div className="mt-8 text-center text-[#363636]/50">
            <p>© {new Date().getFullYear()} streetcred. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}


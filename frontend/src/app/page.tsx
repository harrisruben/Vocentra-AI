"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Phone, Calendar, ArrowRight, ShieldCheck, Zap, Database, MessageSquare, BarChart3, Settings, X, Activity, CheckCircle2 } from "lucide-react";

export default function Home() {
  const [modalContent, setModalContent] = useState<"privacy" | "terms" | "status" | null>(null);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  return (
    <div className="relative min-h-screen bg-[#020617] text-slate-100 flex flex-col font-sans">
      {/* Background Decorative Blobs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none glow-indigo"></div>
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-emerald-600/10 rounded-full blur-[100px] pointer-events-none glow-emerald"></div>

      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <Image 
              src="/logo.png" 
              alt="Vocentra AI Logo" 
              width={32} 
              height={32} 
              className="rounded-lg shadow-lg shadow-indigo-500/10"
              priority
            />
            <span className="premium-logo-text text-xl">
              Vocentra.AI
            </span>
          </Link>

          <div className="flex items-center space-x-4">
            <Link 
              href="/login" 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-slate-800/40"
            >
              Sign In
            </Link>
            <Link 
              href="/signup" 
              className="text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition-all px-4 py-2 rounded-lg shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/30"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-16 md:py-24 z-10">
        <motion.div 
          className="text-center max-w-3xl mx-auto"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 mb-8">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
              Autonomous Voice Technology
            </span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6 leading-[1.1]">
            Turn Inbound Calls Into{" "}
            <span className="gradient-text">Automated Actions</span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-400 mb-10 leading-relaxed">
            Vocentra AI is a production-ready conversational agent. It answers phone calls, schedules appointments, answers support questions using a RAG knowledge base, and syncs CRM systems in the background.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link 
              href="/signup" 
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 text-base font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/30 transition-all group"
            >
              <span>Build Your Voice Agent</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link 
              href="/login" 
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 text-base font-semibold bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white px-8 py-4 rounded-xl transition-all"
            >
              <span>Demo Dashboard</span>
            </Link>
          </div>
        </motion.div>

        {/* Workflow Diagram */}
        <motion.div 
          className="mt-20 glass-panel rounded-2xl p-8 max-w-4xl mx-auto shadow-2xl relative overflow-hidden"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.8 }}
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl"></div>
          <h3 className="text-lg font-bold text-white mb-6 text-center tracking-wide uppercase">
            Platform Orchestration Architecture
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-center items-center">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <Phone className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
              <div className="text-xs font-semibold text-slate-300">Inbound Call</div>
              <div className="text-[10px] text-slate-500 mt-1">Twilio Provider</div>
            </div>
            <div className="text-slate-600 hidden md:block">➔</div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <Zap className="w-8 h-8 text-amber-400 mx-auto mb-2" />
              <div className="text-xs font-semibold text-slate-300">Voice Stream</div>
              <div className="text-[10px] text-slate-500 mt-1">Vapi Orchestration</div>
            </div>
            <div className="text-slate-600 hidden md:block">➔</div>
            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30">
              <Settings className="w-8 h-8 text-indigo-400 mx-auto mb-2 animate-spin-slow" />
              <div className="text-xs font-semibold text-indigo-300">FastAPI Agent</div>
              <div className="text-[10px] text-indigo-400 mt-1">Business Logic & RAG</div>
            </div>
          </div>
        </motion.div>

        {/* Features Grid */}
        <div className="mt-28">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-extrabold tracking-tight text-white mb-4">
              Enterprise Voice Pipelines
            </h2>
            <p className="text-slate-400">
              Designed with low latency, robust state memory, and background workers to keep execution speeds sub-second.
            </p>
          </div>

          <motion.div 
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
          >
            <motion.div className="glass-panel p-8 rounded-2xl glass-card-hover" variants={itemVariants}>
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
                <Zap className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Speech & Intent Pipeline</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Processes incoming audio stream, transcribes it, and detects structural intent (pricing, calendar booking) in real-time.
              </p>
            </motion.div>

            <motion.div className="glass-panel p-8 rounded-2xl glass-card-hover" variants={itemVariants}>
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6">
                <Database className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">pgvector Knowledge Base</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                RAG pipeline enabling the agent to search PDF, FAQs, and company documentation to answer caller queries accurately.
              </p>
            </motion.div>

            <motion.div className="glass-panel p-8 rounded-2xl glass-card-hover" variants={itemVariants}>
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-6">
                <Calendar className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Appointment Scheduling</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Connects directly to calendar availability to hold slots, schedule meetings, and confirm bookings during the call.
              </p>
            </motion.div>

            <motion.div className="glass-panel p-8 rounded-2xl glass-card-hover" variants={itemVariants}>
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-6">
                <MessageSquare className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">CRM Sync & Notifications</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Background worker execution schedules post-call emails, WhatsApp confirmations, and logs leads in HubSpot/Salesforce.
              </p>
            </motion.div>

            <motion.div className="glass-panel p-8 rounded-2xl glass-card-hover" variants={itemVariants}>
              <div className="w-12 h-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-6">
                <BarChart3 className="w-6 h-6 text-pink-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Live Analytics Engine</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Track call duration, token usage, customer sentiments, lead qualification, and response latencies in a single dashboard.
              </p>
            </motion.div>

            <motion.div className="glass-panel p-8 rounded-2xl glass-card-hover" variants={itemVariants}>
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
                <ShieldCheck className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Dockerized Infrastructure</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Spin up frontend, backend, PostgreSQL (with pgvector), Redis, and n8n pipelines together with a single containerized environment.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/40 py-8 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            &copy; {new Date().getFullYear()} Vocentra AI. All rights reserved.
          </div>
          <div className="flex space-x-6">
            <span onClick={() => setModalContent("privacy")} className="hover:text-slate-300 cursor-pointer transition-colors">Privacy Policy</span>
            <span onClick={() => setModalContent("terms")} className="hover:text-slate-300 cursor-pointer transition-colors">Terms of Service</span>
            <span onClick={() => setModalContent("status")} className="hover:text-slate-300 cursor-pointer transition-colors">System Status</span>
          </div>
        </div>
      </footer>

      {/* Modal Overlay */}
      {modalContent && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#020617] border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl relative overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-900 flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                {modalContent === "status" && <Activity className="w-5 h-5 text-indigo-400" />}
                <span>
                  {modalContent === "privacy" && "Privacy Policy"}
                  {modalContent === "terms" && "Terms of Service"}
                  {modalContent === "status" && "System Status"}
                </span>
              </h3>
              <button 
                onClick={() => setModalContent(null)}
                className="p-1.5 bg-slate-900 border border-slate-850 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto flex-grow text-sm text-slate-300 space-y-5 leading-relaxed font-sans scrollbar-thin">
              {modalContent === "privacy" && (
                <>
                  <p className="text-slate-400 text-xs">Last updated: July 16, 2026</p>
                  <div>
                    <h4 className="text-white font-semibold mb-2">1. Data Ownership & Privacy Commitments</h4>
                    <p>Vocentra AI is built with privacy-first standards. The application operates as a business layer over voice provider systems (Vapi). Transcripts, voice recordings, call metadata, and customer profiles are processed and accessed securely in accordance with strict access controls.</p>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">2. Voice Telemetry & Data Collection</h4>
                    <p>To deliver real-time interactive voice agents, we collect caller voice audio and destination phone numbers. Transcripts and recordings are cached dynamically on Vapi trunks during active calling sessions. Vocentra AI does not store persistent local duplicates of private audio recordings.</p>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">3. Compliance and Encryption</h4>
                    <p>All client credentials, API tokens, database keys, and configuration parameters are encrypted in transit using TLS 1.3, and at rest in our secure database configurations using industry-standard AES-256 protocols. The system is designed to support HIPAA and GDPR compliance boundaries.</p>
                  </div>
                </>
              )}

              {modalContent === "terms" && (
                <>
                  <p className="text-slate-400 text-xs">Last updated: July 16, 2026</p>
                  <div>
                    <h4 className="text-white font-semibold mb-2">1. Agreement of Service</h4>
                    <p>By registering an organization workspace on Vocentra AI, you agree to comply with our Acceptable Use policy and understand that voice minutes are billed dynamically against your configured Vapi/Twilio payment providers.</p>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">2. Usage Quotas & Limits</h4>
                    <p>Your subscription tier restricts monthly outbound and inbound dialing sessions. Standard Free organization plans are capped at 100 calls, Growth plans at 1,000 calls, and Enterprise tiers at custom enterprise quotas. Exceeding thresholds will cause outbound requests to yield limit alerts.</p>
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-2">3. Prohibited Use Cases</h4>
                    <p>You agree not to use Vocentra AI to execute spam robocalls, host harassing campaign lines, record conversations without caller notification where legally mandated, or configure unauthorized voice-impersonation pipelines.</p>
                  </div>
                </>
              )}

              {modalContent === "status" && (
                <div className="space-y-6">
                  <div className="flex items-center space-x-3 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                    <div>
                      <h4 className="text-sm font-bold text-white">All Systems Operational</h4>
                      <p className="text-xs text-emerald-400/80 mt-0.5">Real-time status matches healthy SLA benchmarks.</p>
                    </div>
                  </div>

                  <div className="divide-y divide-slate-900 border border-slate-900 rounded-xl overflow-hidden bg-slate-950/20">
                    <div className="flex justify-between items-center p-4">
                      <div>
                        <span className="text-xs font-semibold text-white block">Voice API Gateway</span>
                        <span className="text-[10px] text-slate-500 font-medium">Global proxy routes</span>
                      </div>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">Operational</span>
                    </div>
                    <div className="flex justify-between items-center p-4">
                      <div>
                        <span className="text-xs font-semibold text-white block">Telephony Webhook Handlers</span>
                        <span className="text-[10px] text-slate-500 font-medium">Twilio/Vapi signaling</span>
                      </div>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">Operational</span>
                    </div>
                    <div className="flex justify-between items-center p-4">
                      <div>
                        <span className="text-xs font-semibold text-white block">RAG Vector Cluster</span>
                        <span className="text-[10px] text-slate-500 font-medium">pgvector document indices</span>
                      </div>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">Operational</span>
                    </div>
                    <div className="flex justify-between items-center p-4">
                      <div>
                        <span className="text-xs font-semibold text-white block">Real-time WebSockets</span>
                        <span className="text-[10px] text-slate-500 font-medium">Live telemetry broadcast</span>
                      </div>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">Operational</span>
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-500 font-semibold text-center">
                    Uptime SLA: 99.98% &bull; Incidents in last 90 days: 0
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-slate-900 flex justify-end">
              <button 
                onClick={() => setModalContent(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/30 transition-all"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

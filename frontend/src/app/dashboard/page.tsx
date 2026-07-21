"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useAudioPlayer } from "./useAudioPlayer";
import { 
  Phone, Calendar, BarChart3, Database, Workflow, Settings, Users, Link2, 
  Play, Pause, StopCircle, LogOut, ChevronRight, RefreshCw, AlertCircle, Info, Smile, Frown, Meh, Plus,
  CreditCard, Search, CheckCircle2, Clock, ArrowRight, ShieldAlert, PhoneOff, Copy, Check, Trash, Trash2
} from "lucide-react";

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  
  // Enterprise Console state variables
  const [activeCalls, setActiveCalls] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [selectedCall, setSelectedCall] = useState<any>(null);
  const [dialNumber, setDialNumber] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState("");
  const [tablePage, setTablePage] = useState(1);
  const rowsPerPage = 5;
  const [searchQuery, setSearchQuery] = useState("");
  const [liveTranscript, setLiveTranscript] = useState<any[]>([]);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const audioPlayer = useAudioPlayer(selectedCall?.recordingUrl || null);
  
  // Team invite fields
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  
  // Settings credential fields
  const [twilioSid, setTwilioSid] = useState("");
  const [twilioToken, setTwilioToken] = useState("");
  const [vapiId, setVapiId] = useState("");
  const [n8nUrl, setN8nUrl] = useState("");
  const [callDelay, setCallDelay] = useState(30);

  // Voice logs filtering & pagination
  const [sentimentFilter, setSentimentFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [callLogPage, setCallLogPage] = useState(1);
  const callLogsPerPage = 5;

  // RAG Knowledge state variables
  const [documents, setDocuments] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Billing state variables
  const [billingTier, setBillingTier] = useState("free");
  const [usageLimit, setUsageLimit] = useState(100);
  const [usageCount, setUsageCount] = useState(0);

  // Health Center diagnostics state variables
  const [healthData, setHealthData] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [campaignUploadFile, setCampaignUploadFile] = useState<File | null>(null);
  const [campaignName, setCampaignName] = useState("");
  const [campaignDescription, setCampaignDescription] = useState("");
  const [campaignBusy, setCampaignBusy] = useState(false);
  const [campaignMessage, setCampaignMessage] = useState<string | null>(null);

  // Fetch dashboard stats from backend
  const fetchDashboardData = async () => {
    setLoading(true);
    const token = localStorage.getItem("token");

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error("Failed to load backend stats");
      }

      const data = await response.json();
      setStats(data.data);
      setIsDemoMode(false);
      
      // Auto select first call for timeline detail preview if not set
      if (data.data.recent_calls && data.data.recent_calls.length > 0 && !selectedCall) {
        setSelectedCall(data.data.recent_calls[0]);
      }
    } catch (error) {
      console.warn("Backend unavailable, loading local premium fallback data.", error);
      setIsDemoMode(true);
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  // Poll live active calls
  const fetchActiveCalls = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/active-calls`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (response.ok) {
        const data = await response.json();
        setActiveCalls(data.data);
      }
    } catch (error) {
      console.warn("FastAPI server offline. Loading mockup active calls sandbox data.");
      setActiveCalls([
        {
          call_id: 999,
          customer_name: "Harris Miller",
          customer_phone: "+1 (555) 345-6789",
          active_intent: "booking",
          slots: { date_str: "2026-07-15", title: "Product Demo Consultation" },
          duration: 42,
          last_utterance: "Checking availability for tomorrow morning... I found 10:00 AM open, does that work?",
          llm_latency: 0.78,
          search_latency: 0.038,
          tool_latency: 0.095,
          confidence_score: 98
        }
      ]);
    }
  };

  // Fetch RAG Knowledge documents
  const fetchDocuments = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/rag/documents`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.data);
      }
    } catch (err) {
      console.warn("Offline, loading mock RAG documents.");
      setDocuments([
        { id: 1, title: "Booking & Scheduling FAQ.txt", content_type: "faq", text_preview: "Available slots are 10:00 AM, 1:30 PM, and 3:30 PM. Format strings YYYY-MM-DD. Auto-books via Google Meet.", created_at: new Date().toISOString() },
        { id: 2, title: "Product Pricing Packages.txt", content_type: "text", text_preview: "Enterprise plans start at $1200/month. Standard Growth plans are $199/month. Free starter limit is 100 calls.", created_at: new Date().toISOString() }
      ]);
    }
  };

  // Handle RAG upload selection
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    
    const token = localStorage.getItem("token");
    if (!token) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/rag/upload`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });
      if (response.ok) {
        alert(`Document '${file.name}' uploaded and processed successfully!`);
        fetchDocuments();
      } else {
        const err = await response.json();
        alert(err.detail || "Failed to upload document.");
      }
    } catch (err) {
      alert(`Offline Sandbox: Document '${file.name}' added to mock RAG index.`);
      setDocuments(prev => [
        { id: Date.now(), title: file.name, content_type: "text", text_preview: "Processed chunk in local sandbox environment.", created_at: new Date().toISOString() },
        ...prev
      ]);
    }
  };

  // Fetch Team members and audit logs
  const fetchTeamAndLogs = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const resTeam = await fetch(`${apiHost}/api/v1/dashboard/team`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const resLogs = await fetch(`${apiHost}/api/v1/dashboard/team/audit-logs`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (resTeam.ok) {
        const data = await resTeam.json();
        setTeamMembers(data.data);
      }
      if (resLogs.ok) {
        const data = await resLogs.json();
        setAuditLogs(data.data);
      }
    } catch (err) {
      console.warn("Offline, loading mock team structure.");
      setTeamMembers([
        { id: 1, name: "Dash Tester", email: "dash_tester@vocentra.ai", role: "admin", is_active: true, created_at: new Date().toISOString() }
      ]);
      setAuditLogs([
        { id: 1, action: "api_key_rotated", description: "Rotated Vapi Assistant Webhook Auth Key", ip_address: "127.0.0.1", created_at: new Date().toISOString() }
      ]);
    }
  };

  // Fetch Billing Tier Status
  const fetchBillingStatus = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/billing`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBillingTier(data.data.billing_tier);
        setUsageLimit(data.data.usage_limit);
        setUsageCount(data.data.usage_count);
      }
    } catch (err) {
      console.warn("Offline, loading mock billing status.");
    }
  };

  // Upgrade Billing subscription plan
  const handleUpgradeBilling = async (tier: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/billing/upgrade`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ tier })
      });
      if (response.ok) {
        alert(`Successfully upgraded subscription plan to ${tier}!`);
        fetchBillingStatus();
        fetchTeamAndLogs();
      } else {
        alert("Failed to modify subscription tier.");
      }
    } catch (err) {
      alert(`Offline Sandbox: Plan adjusted to ${tier}.`);
      setBillingTier(tier);
      setUsageLimit(tier === "free" ? 100 : (tier === "growth" ? 1000 : 1000000));
    }
  };

  // Fetch Workspace settings
  const fetchSettings = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/settings`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setTwilioSid(data.data.twilio_sid);
        setTwilioToken(data.data.twilio_token);
        setVapiId(data.data.vapi_assistant_id);
        setN8nUrl(data.data.n8n_webhook_url);
        setCallDelay(data.data.call_delay || 30);
      }
    } catch (err) {
      console.warn("Offline, loading blank settings form.");
    }
  };

  // Save Settings configuration
  const handleSaveSettings = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/settings`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          twilio_sid: twilioSid,
          twilio_token: twilioToken,
          vapi_assistant_id: vapiId,
          n8n_webhook_url: n8nUrl,
          call_delay: callDelay
        })
      });
      if (response.ok) {
        alert("Workspace configuration settings successfully saved!");
        fetchTeamAndLogs();
      } else {
        alert("Failed to save configuration settings.");
      }
    } catch (err) {
      alert("Offline Sandbox: Mock configurations logged locally.");
    }
  };

  // Invite Team Member
  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/team/invite`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email: inviteEmail, name: inviteName, role: inviteRole })
      });
      if (response.ok) {
        setInviteEmail("");
        setInviteName("");
        fetchTeamAndLogs();
        alert("Colleague successfully added to the team!");
      } else {
        const err = await response.json();
        alert(err.message || "Failed to invite member.");
      }
    } catch (err) {
      setTeamMembers(prev => [...prev, { id: Date.now(), name: inviteName, email: inviteEmail, role: inviteRole, is_active: false, created_at: new Date().toISOString() }]);
      setInviteEmail("");
      setInviteName("");
      alert("Offline Sandbox: Invited user added mock record.");
    }
  };

  // Fetch detailed diagnostic health status
  const fetchHealthStatus = async () => {
    setHealthLoading(true);
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/dashboard/health`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setHealthData(data.data);
      }
    } catch (err) {
      console.warn("Offline, loading mock health diagnostics.");
      setHealthData({
        database: { status: "healthy", latency_ms: 12 },
        redis: { status: "healthy", latency_ms: 4 },
        vapi: { status: "healthy", latency_ms: 210 },
        twilio: { status: "healthy" },
        websockets: { status: "healthy", clients_count: 3 },
        knowledge_base: { document_count: 14 },
        last_sync_ago_seconds: 5
      });
    } finally {
      setHealthLoading(false);
    }
  };

  // Trigger Outbound Lead Call session
  const handleTriggerOutboundCall = async (phone: string, name: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/calls/outbound`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ customer_phone: phone, customer_name: name })
      });
      if (response.ok) {
        const data = await response.json();
        const callId = data.data.vapi_call_id;
        
        // Construct and select a temporary call object to open the WebSocket stream
        const placeholderCall = {
          id: data.data.int_call_id,
          vapi_call_id: callId,
          status: "ongoing",
          duration: 0,
          cost: 0.0,
          sentiment: "neutral",
          lead_score: 50,
          created_at: new Date().toISOString(),
          customer: { name, phone },
          summary: "Connecting live outbound call to lead...",
          transcript: ""
        };
        
        // Clear live transcript state
        setLiveTranscript([]);
        
        // Select the call so the WebSocket immediately binds
        handleSelectCall(placeholderCall);
        
        // Refresh dashboard stats list
        fetchDashboardData();
      } else {
        alert("Failed to start outbound call session.");
      }
    } catch (err) {
      alert("Offline Sandbox Mode: Initiating mock outbound call session.");
      const mockCallId = `mock_outbound_${Date.now()}`;
      const placeholderCall = {
        id: Date.now(),
        vapi_call_id: mockCallId,
        status: "ongoing",
        duration: 0,
        cost: 0.0,
        sentiment: "neutral",
        lead_score: 50,
        created_at: new Date().toISOString(),
        customer: { name, phone },
        summary: "Connecting mock outbound call...",
        transcript: ""
      };
      setLiveTranscript([]);
      handleSelectCall(placeholderCall);
    }
  };

  // Terminate an active ongoing call
  const handleEndActiveCall = async (callId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/calls/${callId}/end`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        if (selectedCall && selectedCall.vapi_call_id === callId) {
          setSelectedCall(prev => prev ? { ...prev, status: "completed" } : null);
        }
        fetchDashboardData();
      }
    } catch (err) {
      if (selectedCall && selectedCall.vapi_call_id === callId) {
        setSelectedCall(prev => prev ? { ...prev, status: "completed" } : null);
      }
    }
  };

  // Programmatic click trigger for Next.js developer overlay
  const handleLogoClick = () => {
    try {
      const portal = document.querySelector('nextjs-portal');
      if (portal && portal.shadowRoot) {
        const devButton = 
          portal.shadowRoot.querySelector('button') || 
          portal.shadowRoot.querySelector('[data-nextjs-dialog-trigger]') ||
          portal.shadowRoot.querySelector('div[role="button"]') ||
          portal.shadowRoot.querySelector('[aria-label="Next.js Client-side Dev Overlay"]');
        if (devButton) {
          devButton.click();
        }
      }
    } catch (err) {
      console.warn("Dev Overlay trigger error:", err);
    }
  };

  // Hide the default floating Next.js dev overlay indicator button
  useEffect(() => {
    const hideDefaultDevOverlay = () => {
      try {
        const portal = document.querySelector('nextjs-portal');
        if (portal && portal.shadowRoot) {
          const button = portal.shadowRoot.querySelector('button');
          if (button) {
            button.style.opacity = '0';
            button.style.pointerEvents = 'none';
            button.style.position = 'absolute';
            button.style.left = '-9999px';
          }
        }
      } catch (err) {
        // Safe fail
      }
    };

    const interval = setInterval(hideDefaultDevOverlay, 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync selected call customer phone to outbound dialer input
  useEffect(() => {
    if (selectedCall && selectedCall.customer) {
      setDialNumber(selectedCall.customer.phone || "");
    } else {
      setDialNumber("");
    }
  }, [selectedCall]);

  useEffect(() => {
    fetchDashboardData();
    
    // Setup WebSocket connection for live call telemetry
    const token = localStorage.getItem("token");
    if (!token) return;

    const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = apiHost.replace(/^https?:\/\//, "");
    
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      console.log("WebSocket: Connecting to active calls stream...");
      socket = new WebSocket(`${wsProtocol}//${wsHost}/api/v1/ws/dashboard?token=${token}`);

      socket.onopen = () => {
        console.log("WebSocket: Connected for live telemetry updates.");
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload && payload.type === "active_calls") {
            setActiveCalls(payload.data);
          } else if (payload && payload.type === "campaign_progress") {
            const updated = payload.data;
            setCampaigns(prev => 
              prev.map(c => 
                c.id === updated.campaign_id 
                  ? { 
                      ...c, 
                      status: updated.status, 
                      completed_count: updated.completed_count, 
                      failed_count: updated.failed_count, 
                      lead_count: updated.lead_count,
                      stats: updated
                    } 
                  : c
              )
            );
          } else if (payload && payload.type === "campaign_deleted") {
            const deletedId = payload.campaign_id;
            console.log("WebSocket: Campaign deletion received. Removing campaign ID =", deletedId);
            setCampaigns(prev => prev.filter(c => c.id !== deletedId));
          }
        } catch (err) {
          console.warn("WebSocket: Error parsing active calls payload", err);
        }
      };

      socket.onerror = (error) => {
        console.warn("WebSocket: Active calls stream status update", error);
      };

      socket.onclose = (event) => {
        console.log(`WebSocket: Closed (code: ${event.code}). Attempting reconnect in 4s...`);
        if (event.code !== 1000 && event.code !== 1008) {
          reconnectTimeout = setTimeout(connectWebSocket, 4000);
        }
      };
    };

    connectWebSocket();

    // Fallback polling loop (at lower rate) if socket is disconnected or not supported
    const fallbackInterval = setInterval(() => {
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        fetchActiveCalls();
      }
    }, 8000);

    return () => {
      if (socket) {
        socket.close(1000);
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      clearInterval(fallbackInterval);
    };
  }, []);

  // Fetch relevant records on tab selection
  useEffect(() => {
    if (activeTab === "team") {
      fetchTeamAndLogs();
    } else if (activeTab === "knowledge") {
      fetchDocuments();
    } else if (activeTab === "billing") {
      fetchBillingStatus();
    } else if (activeTab === "settings") {
      fetchSettings();
    } else if (activeTab === "health") {
      fetchHealthStatus();
    } else if (activeTab === "campaigns") {
      fetchCampaigns();
    }
  }, [activeTab]);

  // Telemetry auto-refresh polling interval when Health Center is active
  useEffect(() => {
    if (activeTab !== "health") return;
    
    const interval = setInterval(() => {
      fetchHealthStatus();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [activeTab]);

  const loadMockData = () => {
    const defaultCalls = [
      {
        id: 101,
        customer: { name: "Alice Cooper", phone: "+1 (555) 789-0123", email: "alice@cooper.com" },
        duration: 94,
        sentiment: "positive",
        lead_score: 95,
        cost: 0.28,
        summary: "Alice requested pricing guidelines for the SaaS Growth Tier and was qualified as an enterprise lead. Confirmation sent.",
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 102,
        customer: { name: "Bob Peterson", phone: "+1 (555) 234-5678", email: "bob@peterson.com" },
        duration: 112,
        sentiment: "neutral",
        lead_score: 70,
        cost: 0.34,
        summary: "Bob called to book a follow-up scheduler slot. Successfully scheduled consultation call for Thursday afternoon.",
        created_at: new Date(Date.now() - 7200000).toISOString()
      }
    ];

    setStats({
      today_calls: { title: "Today's Calls", value: "18", change: "+35% from yesterday", type: "positive" },
      active_calls: { title: "Active Calls", value: "1", change: "Live caller on line", type: "neutral" },
      appointments: { title: "Appointments Booked", value: "8", change: "100% booking rate", type: "positive" },
      revenue: { title: "Pipeline Value", value: "$9,600", change: "+12% this week", type: "positive" },
      recent_calls: defaultCalls,
      upcoming_appointments: [
        {
          id: 1,
          customer: { name: "Alice Cooper", phone: "+1 (555) 789-0123", email: "alice@cooper.com" },
          title: "Vocentra AI Product Demo",
          start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          status: "scheduled",
          notes: "Auto-scheduled demo session from inbound call conversation."
        }
      ]
    });
    
    if (!selectedCall) {
      setSelectedCall(defaultCalls[0]);
    }
  };

  const handleSelectCall = async (call: any) => {
    setSelectedCall(call);
    setLiveTranscript([]);
    setDetailError(null);
    setDetailLoading(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setDetailLoading(false);
      return;
    }

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/calls/${call.id}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const resJson = await response.json();
        const resolvedCall = { ...call, ...resJson.data };
        setSelectedCall(resolvedCall);

        const recordingResponse = await fetch(`${apiHost}/api/v1/calls/${call.id}/recording`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (recordingResponse.ok) {
          const recordingData = await recordingResponse.json();
          setSelectedCall({ ...resolvedCall, recordingUrl: recordingData?.data?.recordingUrl || resolvedCall.recordingUrl });
        }
      } else {
        const errText = await response.text();
        throw new Error(errText || "Unable to retrieve call details.");
      }
    } catch (err) {
      console.warn("Failed to load call details.", err);
      setDetailError("Unable to retrieve call details.");
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    if (!selectedCall || selectedCall.status !== "ongoing") {
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) return;

    const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = apiHost.replace(/^https?:\/\//, "");

    console.log(`WebSocket: Connecting to live transcripts stream for call ${selectedCall.vapi_call_id}...`);
    const tSocket = new WebSocket(`${wsProtocol}//${wsHost}/api/v1/ws/transcripts?call_id=${selectedCall.vapi_call_id}&token=${token}`);

    tSocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("WebSocket: Live transcript chunk received:", message);
        setLiveTranscript(prev => [...prev, message]);
      } catch (err) {
        console.warn("WebSocket: Error parsing transcript message", err);
      }
    };

    tSocket.onerror = (error) => {
      console.warn("WebSocket: Transcript stream encountered update", error);
    };

    const cSocket = new WebSocket(`${wsProtocol}//${wsHost}/api/v1/ws/calls?token=${token}`);
    cSocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message?.vapi_call_id === selectedCall.vapi_call_id && ["completed", "ended", "failed"].includes(String(message.status || "").toLowerCase())) {
          void handleSelectCall(selectedCall);
        }
      } catch (err) {
        console.warn("WebSocket: Error parsing call event", err);
      }
    };

    cSocket.onerror = (error) => {
      console.warn("WebSocket: Call status stream encountered update", error);
    };

    return () => {
      tSocket.close();
      cSocket.close();
    };
  }, [selectedCall?.vapi_call_id, selectedCall?.status]);

  const fetchCampaigns = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/campaigns`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.data || []);
      }
    } catch (err) {
      console.warn("Campaigns unavailable in offline sandbox.", err);
      setCampaigns([]);
    }
  };

  const handleCampaignUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token || !campaignUploadFile) return;

    setCampaignBusy(true);
    setCampaignMessage(null);

    const formData = new FormData();
    formData.append("file", campaignUploadFile);
    formData.append("campaign_name", campaignName || "Bulk Calling Campaign");
    formData.append("description", campaignDescription);

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/campaigns/upload`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Unable to upload contacts");
      setCampaignMessage(`Uploaded ${payload.data.lead_count} leads into campaign ${payload.data.campaign_id}.`);
      setCampaignName("");
      setCampaignDescription("");
      setCampaignUploadFile(null);
      await fetchCampaigns();
    } catch (err: any) {
      setCampaignMessage(err.message || "Unable to upload campaign file.");
    } finally {
      setCampaignBusy(false);
    }
  };

  const handleCampaignStart = async (campaignId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/campaigns/${campaignId}/start`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Unable to start campaign");
      await fetchCampaigns();
      setCampaignMessage(`Campaign ${campaignId} started successfully.`);
    } catch (err: any) {
      setCampaignMessage(err.message || "Unable to start campaign.");
    }
  };

  const handleCampaignPause = async (campaignId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/campaigns/${campaignId}/pause`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Unable to pause campaign");
      await fetchCampaigns();
      setCampaignMessage(`Campaign ${campaignId} paused successfully.`);
    } catch (err: any) {
      setCampaignMessage(err.message || "Unable to pause campaign.");
    }
  };

  const handleCampaignResume = async (campaignId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/campaigns/${campaignId}/resume`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Unable to resume campaign");
      await fetchCampaigns();
      setCampaignMessage(`Campaign ${campaignId} resumed successfully.`);
    } catch (err: any) {
      setCampaignMessage(err.message || "Unable to resume campaign.");
    }
  };

  const handleCampaignRetryFailed = async (campaignId: number) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiHost}/api/v1/campaigns/${campaignId}/retry-failed`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Unable to retry failed leads");
      await fetchCampaigns();
      setCampaignMessage(`Retrying failed leads for campaign ${campaignId}.`);
    } catch (err: any) {
      setCampaignMessage(err.message || "Unable to retry failed leads.");
    }
  };

  const handleCampaignDelete = async (campaignId: number) => {
    console.log("Delete Flow: Delete Button Clicked. campaignId =", campaignId);
    const confirmDelete = window.confirm("This will permanently delete the campaign and all associated lead history.");
    if (!confirmDelete) {
      console.log("Delete Flow: Confirmation Rejected.");
      return;
    }
    console.log("Delete Flow: Confirmation Accepted.");

    const token = localStorage.getItem("token");
    if (!token) {
      console.error("Delete Flow failed: Stage = Frontend, Reason = Missing auth token");
      setCampaignMessage("Authentication token is missing. Please log in again.");
      return;
    }

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const endpoint = `${apiHost}/api/v1/campaigns/${campaignId}`;
      console.log("Delete Flow: Sending DELETE Request to", endpoint);
      
      const response = await fetch(endpoint, {
        method: "DELETE",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      const payload = await response.json();
      console.log("Delete Flow: Received Response", response.status, payload);

      if (!response.ok || !payload.success) {
        const stage = payload.stage || "Network";
        const reason = payload.reason || payload.message || "Failed to delete campaign";
        throw new Error(`[Stage: ${stage}] ${reason}`);
      }
      
      console.log("Delete Flow: Successful. Refreshing campaigns UI.");
      await fetchCampaigns();
      setCampaignMessage(`Campaign successfully deleted.`);
      console.log("Delete Flow: Frontend Updated.");
    } catch (err: any) {
      console.error("Delete Flow failed: Stage = Frontend, Reason =", err.message || err);
      setCampaignMessage(err.message || "Unable to delete campaign.");
    }
  };

  const handleCallDelete = async (callId: number | string) => {
    console.log("Delete Flow: Delete Call Button Clicked. callId =", callId);
    const confirmDelete = window.confirm("This will permanently delete this call record from Vocentra database logs.");
    if (!confirmDelete) {
      console.log("Delete Flow: Call Confirmation Rejected.");
      return;
    }
    console.log("Delete Flow: Call Confirmation Accepted.");

    const token = localStorage.getItem("token");
    if (!token) {
      console.error("Delete Flow failed: Stage = Frontend, Reason = Missing auth token");
      alert("Authentication token is missing. Please log in again.");
      return;
    }

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const endpoint = `${apiHost}/api/v1/calls/${callId}`;
      console.log("Delete Flow: Sending DELETE Call Request to", endpoint);

      const response = await fetch(endpoint, {
        method: "DELETE",
        headers: { 
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      const payload = await response.json();
      console.log("Delete Flow: Received Call Response", response.status, payload);

      if (!response.ok || !payload.success) {
        const stage = payload.stage || "Network";
        const reason = payload.reason || payload.message || "Failed to delete call record";
        throw new Error(`[Stage: ${stage}] ${reason}`);
      }

      console.log("Delete Flow: Call successful. Refreshing calls UI.");
      if (selectedCall && (selectedCall.id === callId || selectedCall.vapi_call_id === callId)) {
        setSelectedCall(null);
      }
      await fetchDashboardData();
      alert("Call history log successfully deleted.");
      console.log("Delete Flow: Call Frontend Updated.");
    } catch (err: any) {
      console.error("Delete Flow failed: Stage = Frontend, Reason =", err.message || err);
      alert(err.message || "Unable to delete call record.");
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <Smile className="w-4 h-4 text-emerald-400" />;
      case "negative":
        return <Frown className="w-4 h-4 text-rose-400" />;
      default:
        return <Meh className="w-4 h-4 text-indigo-400" />;
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds && seconds !== 0) return "0s";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
    }
    return `${secs}s`;
  };

  const formatCurrency = (value: number | string | undefined) => {
    const parsed = typeof value === "number" ? value : Number(value || 0);
    return `$${parsed.toFixed(2)}`;
  };

  const getSpeakerLabel = (message: any) => {
    if (message?.role === "user") return "Customer";
    if (message?.role === "assistant") return "AI";
    if (message?.role === "tool") return "Tool";
    return message?.speaker || "System";
  };

  const formatLocalStartTime = (dateString: string) => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      const utc = date.getTime() + (date.getTimezoneOffset() * 60000);
      const localTime = new Date(utc + (3600000 * 5.5)); // Force GMT+5:30 shift
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const month = months[localTime.getMonth()];
      const day = localTime.getDate();
      const year = localTime.getFullYear();
      const hours = String(localTime.getHours()).padStart(2, "0");
      const minutes = String(localTime.getMinutes()).padStart(2, "0");
      return `${month} ${day}, ${year}, ${hours}:${minutes}`;
    } catch (e) {
      return dateString;
    }
  };

  const handleCopyToClipboard = (text: string, id: string) => {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const menuItems = [
    { id: "dashboard", label: "Dashboard Metrics", icon: BarChart3 },
    { id: "campaigns", label: "Bulk Campaigns", icon: Workflow },
    { id: "calls", label: "Voice Call Logs", icon: Phone },
    { id: "knowledge", label: "RAG Knowledge Base", icon: Database },
    { id: "team", label: "Team Members", icon: Users },
    { id: "billing", label: "Billing & Quota", icon: CreditCard },
    { id: "settings", label: "Workspace Settings", icon: Settings },
    { id: "health", label: "AI Health Center", icon: ShieldAlert },
  ];

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 flex font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-900 bg-slate-950/40 shrink-0 hidden md:flex flex-col p-6">
        <div 
          onClick={handleLogoClick}
          className="flex items-center space-x-2 mb-10 cursor-pointer hover:opacity-85 select-none transition-all active:scale-95"
          title="Toggle Developer Operations Overlay"
        >
          <div className="w-9 h-9 flex items-center justify-center relative">
            <Image 
              src="/logo.png" 
              alt="Vocentra AI Logo" 
              width={36} 
              height={36} 
              className="rounded-lg"
              priority
            />
          </div>
          <span className="premium-logo-text text-lg">
            Vocentra.AI
          </span>
        </div>

        <nav className="flex-grow space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all text-left ${
                  isActive 
                    ? "bg-indigo-600/10 text-indigo-400 border-l-2 border-indigo-500" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                }`}
              >
                <Icon className="w-4.5 h-4.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="pt-6 border-t border-slate-900 space-y-3">
          <div className="flex items-center space-x-3 px-2">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-semibold text-white">
              V
            </div>
            <div>
              <div className="text-xs font-bold text-white">Vocentra Work Space</div>
              <div className="text-[10px] text-slate-500">Premium Account</div>
            </div>
          </div>
          <button 
            onClick={handleSignOut}
            className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-lg text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/5 transition-all text-left"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-grow flex flex-col min-w-0">
        <header className="border-b border-slate-900 bg-slate-950/20 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight text-white capitalize">
            {activeTab.replace("-", " ")}
          </h1>
          <div className="flex items-center space-x-4">
            <button 
              onClick={fetchDashboardData}
              className="p-2 border border-slate-850 hover:bg-slate-900 rounded-lg text-slate-400 hover:text-white transition-all"
              title="Refresh Stats"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <div className="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              <span>Voice Agent: Active</span>
            </div>
          </div>
        </header>

        <main className="flex-grow p-6 overflow-y-auto max-w-7xl w-full mx-auto">
          {isDemoMode && (
            <div className="mb-8 p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-start space-x-3">
              <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-indigo-300">FastAPI Server Not Detected (Offline Sandbox Mode)</h4>
                <p className="text-xs text-slate-400 mt-1">
                  The dashboard is rendering cached templates. Start the backend app via `uvicorn` to synchronize database records in real-time.
                </p>
              </div>
            </div>
          )}

          {loading ? (
            <div className="min-h-[400px] flex items-center justify-center">
              <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
          ) : activeTab === "campaigns" ? (
            <div className="space-y-8">
              <div className="glass-panel p-6 rounded-2xl border border-slate-900">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Bulk Calling Campaigns</h3>
                    <p className="text-sm text-slate-400 mt-1">Upload a CSV of contacts, queue calls through Vapi, and monitor the live execution state.</p>
                  </div>
                </div>
                <form onSubmit={handleCampaignUpload} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input value={campaignName} onChange={(e) => setCampaignName(e.target.value)} className="bg-slate-950 border border-slate-900 rounded-xl px-4 py-3 text-sm text-white" placeholder="Campaign name" required />
                    <input value={campaignDescription} onChange={(e) => setCampaignDescription(e.target.value)} className="bg-slate-950 border border-slate-900 rounded-xl px-4 py-3 text-sm text-white" placeholder="Description" />
                  </div>
                  <input type="file" accept=".csv,.xlsx,.xls,.xlsm" onChange={(e) => setCampaignUploadFile(e.target.files?.[0] || null)} className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-500/10 file:text-indigo-400" required />
                  <div className="flex items-center space-x-3">
                    <button type="submit" disabled={campaignBusy} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold disabled:opacity-60">
                      {campaignBusy ? "Uploading..." : "Upload and queue campaign"}
                    </button>
                    <span className="text-sm text-slate-400">CSV columns: name, phone, email</span>
                  </div>
                </form>
                {campaignMessage ? <p className="mt-4 text-sm text-emerald-400">{campaignMessage}</p> : null}
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-slate-900">
                <h3 className="text-lg font-semibold text-white mb-4">Recent Campaigns</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {campaigns.length === 0 ? (
                    <p className="text-sm text-slate-400 col-span-2">No campaigns yet. Upload a CSV to create the first one.</p>
                  ) : campaigns.map((campaign: any) => {
                    const totalFinished = (campaign.completed_count || 0) + (campaign.failed_count || 0);
                    const progressPct = Math.round((totalFinished / campaign.lead_count * 100) || 0);
                    
                    const filledBlocks = Math.round(progressPct / 10);
                    const emptyBlocks = 10 - filledBlocks;
                    const progressBarStr = "█".repeat(filledBlocks) + "░".repeat(emptyBlocks) + ` ${progressPct}%`;
                    
                    const wsStats = campaign.stats || {};
                    const totalCost = wsStats.total_cost !== undefined ? wsStats.total_cost : 0.0;
                    const etaSeconds = wsStats.eta_seconds !== undefined ? wsStats.eta_seconds : 0;
                    
                    const formatEta = (secs: number) => {
                      if (secs <= 0) return "N/A";
                      const h = Math.floor(secs / 3600);
                      const m = Math.floor((secs % 3600) / 60);
                      if (h > 0) return `${h}h ${m}m`;
                      return `${m}m`;
                    };

                    const statusBadgeColors = (status: string) => {
                      switch (status) {
                        case "running": return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                        case "paused": return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
                        case "completed": return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
                        default: return "bg-slate-900 text-slate-400 border border-slate-800";
                      }
                    };

                    return (
                      <div key={campaign.id} className="p-5 rounded-2xl border border-slate-900 bg-slate-950/40 hover:bg-slate-950/60 transition-all duration-300 relative group flex flex-col justify-between hover:border-slate-800 gap-4">
                        <div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors truncate">{campaign.name}</span>
                            <span className={`text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${statusBadgeColors(campaign.status)}`}>
                              {campaign.status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">{campaign.description || "Bulk calling outbound campaign"}</p>
                          
                          {/* Animated Progress Section */}
                          <div className="mt-4 space-y-2">
                            <div className="flex justify-between text-[11px] font-mono text-slate-400">
                              <span>Progress</span>
                              <span>{progressBarStr}</span>
                            </div>
                            <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden relative">
                              <div 
                                className={`h-full rounded-full transition-all duration-500 ${campaign.status === "running" ? "bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 animate-pulse" : "bg-indigo-650"}`}
                                style={{ width: `${progressPct}%` }}
                              ></div>
                            </div>
                          </div>

                          {/* Stats Grid */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-900/60 text-[10px] text-slate-400 font-medium">
                            <div>
                              <span className="text-slate-500 block">Total Leads</span>
                              <span className="text-white font-bold">{campaign.lead_count}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Completions</span>
                              <span className="text-emerald-400 font-bold">{campaign.completed_count || 0}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Failed Calls</span>
                              <span className="text-rose-400 font-bold">{campaign.failed_count || 0}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">ETA</span>
                              <span className="text-cyan-400 font-bold font-mono">{formatEta(etaSeconds)}</span>
                            </div>
                          </div>
                        </div>

                        {/* Control buttons & Cost info */}
                        <div className="flex items-center justify-between pt-3 border-t border-slate-900/60 mt-2">
                          <span className="text-[11px] font-semibold text-slate-400">
                            Cost: <span className="font-bold text-emerald-400 font-mono">${totalCost.toFixed(2)}</span>
                          </span>

                          <div className="flex items-center space-x-1.5">
                            {campaign.status === "draft" && (
                              <button onClick={() => handleCampaignStart(campaign.id)} className="px-3 py-1.5 rounded-xl bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 text-xs font-bold transition-all">Start</button>
                            )}
                            {campaign.status === "running" && (
                              <button onClick={() => handleCampaignPause(campaign.id)} className="px-3 py-1.5 rounded-xl bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 text-xs font-bold transition-all">Pause</button>
                            )}
                            {campaign.status === "paused" && (
                              <button onClick={() => handleCampaignResume(campaign.id)} className="px-3 py-1.5 rounded-xl bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 text-xs font-bold transition-all">Resume</button>
                            )}
                            {(campaign.status === "completed" || campaign.failed_count > 0) && (
                              <button onClick={() => handleCampaignRetryFailed(campaign.id)} className="px-3 py-1.5 rounded-xl bg-indigo-650/20 text-indigo-400 hover:bg-indigo-650/30 text-xs font-bold transition-all">Retry Failed</button>
                            )}
                            <button onClick={() => handleCampaignDelete(campaign.id)} className="p-1.5 rounded-xl bg-rose-500/10 text-rose-500 hover:bg-rose-500/20 transition-all" title="Delete Campaign">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : activeTab === "dashboard" ? (
            // --- DASHBOARD TAB ---
            <div className="space-y-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {Object.keys(stats || {}).filter(k => typeof stats[k] === "object" && !Array.isArray(stats[k])).map((key) => {
                  const widget = stats[key];
                  return (
                    <div key={key} className="glass-panel p-6 rounded-2xl border border-slate-900 glow-indigo relative overflow-hidden">
                      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider block mb-2">{widget.title}</span>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{widget.value}</span>
                      </div>
                      <span className="text-[10px] text-emerald-400 font-semibold mt-2 block">{widget.change}</span>
                    </div>
                  );
                })}
              </div>

              {/* Live Call Monitor Console */}
              {activeCalls.length > 0 && (
                <div className="glass-panel p-6 rounded-2xl border border-slate-900 glow-indigo relative overflow-hidden">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Call Console Stream</h3>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {activeCalls.map((call: any) => (
                      <div key={call.call_id} className="p-4 bg-slate-950/60 rounded-xl border border-slate-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="min-w-0 flex-grow">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm font-bold text-white">{call.customer_name}</span>
                            <span className="text-xs text-slate-500 font-mono">{call.customer_phone}</span>
                            <span className="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2.5 py-0.5 rounded-full uppercase font-bold tracking-wider">
                              Intent: {call.active_intent}
                            </span>
                          </div>
                          <div className="mt-2.5 p-3 bg-slate-900/40 border border-slate-855 rounded-lg flex items-center space-x-2">
                            <Play className="w-3.5 h-3.5 text-emerald-400 shrink-0 animate-pulse" />
                            <p className="text-xs italic text-slate-300">&ldquo;{call.last_utterance}&rdquo;</p>
                          </div>
                        </div>

                        {/* Active Parameter Slots & Latency Telemetry */}
                        <div className="flex flex-wrap items-center gap-6 shrink-0 text-xs mt-2 md:mt-0 md:border-l md:border-slate-900 md:pl-6">
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Target Date</span>
                            <span className="font-mono text-indigo-300 font-bold">{call.slots?.date_str || "checking..."}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Meeting Title</span>
                            <span className="text-slate-300 font-medium truncate max-w-[120px] block">{call.slots?.title || "N/A"}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">LLM Speed</span>
                            <span className="font-mono text-emerald-400 font-bold">{call.llm_latency || "0.78"}s</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">RAG Match</span>
                            <span className="font-mono text-indigo-400 font-bold">{call.search_latency || "0.038"}s</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">AI Confidence</span>
                            <span className={`font-mono font-bold ${(call.confidence_score || 95) >= 95 ? "text-emerald-400" : "text-amber-400"}`}>{call.confidence_score || "95"}%</span>
                          </div>
                          <div className="text-right">
                            <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Duration</span>
                            <span className="font-mono text-slate-300 font-bold">{call.duration}s</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Call Records & Appointments Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col">
                  {/* Header & Local Search */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                    <h3 className="text-base font-bold text-white">Recent Call Sessions</h3>
                    <div className="flex items-center space-x-3">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                        <input 
                          type="text" 
                          placeholder="Search calls..." 
                          value={tableSearch}
                          onChange={(e) => { setTableSearch(e.target.value); setTablePage(1); }}
                          className="pl-9 pr-4 py-1.5 bg-slate-950 border border-slate-900 rounded-xl text-xs text-slate-300 placeholder-slate-650 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 w-44"
                        />
                      </div>
                      <button onClick={() => setActiveTab("calls")} className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1 shrink-0">
                        <span>View All Logs</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Desktop/Tablet Layout - Full Table */}
                  <div className="hidden md:block overflow-x-auto min-h-[200px]">
                    <table className="w-full text-left text-sm border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                          <th className="pb-3 pr-4">Call ID</th>
                          <th className="pb-3 px-4">Assistant Phone</th>
                          <th className="pb-3 px-4">Customer Phone</th>
                          <th className="pb-3 px-4">Type</th>
                          <th className="pb-3 px-4">Ended Reason</th>
                          <th className="pb-3 px-4">Start Time</th>
                          <th className="pb-3 px-4">Duration</th>
                          <th className="pb-3 pl-4 text-right">Cost</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-900">
                        {loading ? (
                          Array.from({ length: 5 }).map((_, idx) => (
                            <tr key={idx} className="animate-pulse border-b border-slate-900/40">
                              <td className="py-4 pr-4"><div className="h-4 bg-slate-900 rounded w-16"></div></td>
                              <td className="py-4 px-4"><div className="h-4 bg-slate-900 rounded w-24"></div></td>
                              <td className="py-4 px-4"><div className="h-4 bg-slate-900 rounded w-24"></div></td>
                              <td className="py-4 px-4"><div className="h-6 bg-slate-900 rounded-full w-16"></div></td>
                              <td className="py-4 px-4"><div className="h-6 bg-slate-900 rounded w-14"></div></td>
                              <td className="py-4 px-4"><div className="h-4 bg-slate-900 rounded w-28"></div></td>
                              <td className="py-4 px-4"><div className="h-4 bg-slate-900 rounded w-12"></div></td>
                              <td className="py-4 pl-4 text-right"><div className="h-4 bg-slate-900 rounded w-10 ml-auto"></div></td>
                            </tr>
                          ))
                        ) : (() => {
                          const callsList = stats?.recent_calls || [];
                          const sortedCalls = [...callsList].sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                          const filteredCalls = sortedCalls.filter((c: any) => {
                            const searchLower = tableSearch.toLowerCase();
                            const matchCallId = c.vapi_call_id?.toLowerCase().includes(searchLower) || false;
                            const matchAssistant = c.twilio_call_id?.toLowerCase().includes(searchLower) || "+19843712375".includes(searchLower) || false;
                            const matchCustomer = c.customer?.phone?.toLowerCase().includes(searchLower) || c.customer?.name?.toLowerCase().includes(searchLower) || false;
                            const matchType = c.type?.toLowerCase().includes(searchLower) || false;
                            const matchReason = c.ended_reason?.toLowerCase().includes(searchLower) || false;
                            return matchCallId || matchAssistant || matchCustomer || matchType || matchReason;
                          });

                          const totalPages = Math.ceil(filteredCalls.length / rowsPerPage) || 1;
                          const paginatedCalls = filteredCalls.slice((tablePage - 1) * rowsPerPage, tablePage * rowsPerPage);

                          if (paginatedCalls.length === 0) {
                            return (
                              <tr>
                                <td colSpan={8} className="py-12 text-center text-slate-500">
                                  <div className="flex flex-col items-center justify-center space-y-2">
                                    <Phone className="w-8 h-8 text-slate-600 animate-pulse" />
                                    <span className="text-xs font-medium">No recent calls available</span>
                                  </div>
                                </td>
                              </tr>
                            );
                          }

                          return paginatedCalls.map((call: any) => {
                            const isOutbound = call.type === "outboundPhoneCall" || !call.type?.toLowerCase().includes("inbound");
                            return (
                              <tr 
                                key={call.id} 
                                onClick={() => { handleSelectCall(call); setActiveTab("calls"); }} 
                                className="group hover:bg-slate-900/20 transition-all cursor-pointer"
                              >
                                {/* Call ID */}
                                <td className="py-3.5 pr-4 font-mono text-xs text-indigo-400 group/cell relative">
                                  <div className="flex items-center space-x-1.5 cursor-help" title={call.vapi_call_id}>
                                    <span>{call.vapi_call_id ? `${call.vapi_call_id.substring(0, 4)}...${call.vapi_call_id.slice(-4)}` : "N/A"}</span>
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleCopyToClipboard(call.vapi_call_id || "", `id-${call.id}`);
                                      }}
                                      className="opacity-0 group-hover/cell:opacity-100 p-1 hover:bg-slate-850 rounded transition-all"
                                    >
                                      {copiedId === `id-${call.id}` ? (
                                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                                      ) : (
                                        <Copy className="w-3.5 h-3.5 text-slate-500 hover:text-slate-350" />
                                      )}
                                    </button>
                                  </div>
                                </td>
                                {/* Assistant Phone */}
                                <td className="py-3.5 px-4 text-xs font-medium text-slate-300 group/assistant">
                                  <div className="flex items-center space-x-1">
                                    <span>+1 (984) 371-2375</span>
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleCopyToClipboard("+19843712375", `asst-${call.id}`);
                                      }}
                                      className="opacity-0 group-hover/assistant:opacity-100 p-1 hover:bg-slate-850 rounded transition-all"
                                    >
                                      {copiedId === `asst-${call.id}` ? (
                                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                                      ) : (
                                        <Copy className="w-3.5 h-3.5 text-slate-500 hover:text-slate-350" />
                                      )}
                                    </button>
                                  </div>
                                  <span className="inline-block mt-1 text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-slate-900/60 border border-slate-850 text-slate-500 uppercase tracking-wider">
                                    Vapi
                                  </span>
                                </td>
                                {/* Customer Phone */}
                                <td className="py-3.5 px-4 text-xs font-semibold text-white group/customer font-mono">
                                  <div className="flex items-center space-x-1">
                                    <span>{call.customer?.phone || "+15550199000"}</span>
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleCopyToClipboard(call.customer?.phone || "", `cust-${call.id}`);
                                      }}
                                      className="opacity-0 group-hover/customer:opacity-100 p-1 hover:bg-slate-855 rounded transition-all"
                                    >
                                      {copiedId === `cust-${call.id}` ? (
                                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                                      ) : (
                                        <Copy className="w-3.5 h-3.5 text-slate-500 hover:text-slate-350" />
                                      )}
                                    </button>
                                  </div>
                                </td>
                                {/* Type */}
                                <td className="py-3.5 px-4 text-xs">
                                  {isOutbound ? (
                                    <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                      Outbound
                                    </span>
                                  ) : (
                                    <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                      Inbound
                                    </span>
                                  )}
                                </td>
                                {/* Ended Reason */}
                                <td className="py-3.5 px-4 text-xs">
                                  <span className="inline-flex px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-slate-900/60 border border-slate-850 text-slate-450 capitalize">
                                    {call.ended_reason ? call.ended_reason.replace("-ended-call", "").replace("-", " ") : "Customer"}
                                  </span>
                                </td>
                                {/* Start Time */}
                                <td className="py-3.5 px-4 text-xs text-slate-400 whitespace-nowrap">
                                  {formatLocalStartTime(call.created_at)}
                                </td>
                                {/* Duration */}
                                <td className="py-3.5 px-4 text-xs font-mono text-slate-300">
                                  {formatDuration(call.duration)}
                                </td>
                                {/* Cost */}
                                <td className="py-3.5 pl-4 text-xs text-right font-mono text-emerald-400 font-bold">
                                  ${(call.cost || 0).toFixed(2)}
                                </td>
                              </tr>
                            );
                          });
                        })()}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Layout - Expandable Cards */}
                  <div className="md:hidden space-y-4">
                    {loading ? (
                      Array.from({ length: 3 }).map((_, idx) => (
                        <div key={idx} className="p-4 bg-slate-900/20 border border-slate-900 rounded-xl animate-pulse space-y-3">
                          <div className="flex justify-between"><div className="h-4 bg-slate-900 rounded w-20"></div><div className="h-4 bg-slate-900 rounded w-12"></div></div>
                          <div className="h-3 bg-slate-900 rounded w-32"></div>
                          <div className="h-3 bg-slate-900 rounded w-24"></div>
                        </div>
                      ))
                    ) : (() => {
                      const callsList = stats?.recent_calls || [];
                      const sortedCalls = [...callsList].sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                      const filteredCalls = sortedCalls.filter((c: any) => {
                        const searchLower = tableSearch.toLowerCase();
                        const matchCallId = c.vapi_call_id?.toLowerCase().includes(searchLower) || false;
                        const matchAssistant = c.twilio_call_id?.toLowerCase().includes(searchLower) || (c.type === "inboundPhoneCall" && "+19843712375".includes(searchLower)) || false;
                        const matchCustomer = c.customer?.phone?.toLowerCase().includes(searchLower) || false;
                        return matchCallId || matchAssistant || matchCustomer;
                      });

                      const paginatedCalls = filteredCalls.slice((tablePage - 1) * rowsPerPage, tablePage * rowsPerPage);

                      if (paginatedCalls.length === 0) {
                        return (
                          <div className="p-8 text-center text-slate-500 flex flex-col items-center justify-center space-y-2">
                            <Phone className="w-8 h-8 text-slate-600" />
                            <span className="text-xs font-medium">No recent calls available</span>
                          </div>
                        );
                      }

                      return paginatedCalls.map((call: any) => {
                        const isOutbound = call.type === "outboundPhoneCall" || !call.type?.toLowerCase().includes("inbound");
                        return (
                          <div 
                            key={call.id} 
                            onClick={() => { handleSelectCall(call); setActiveTab("calls"); }}
                            className="p-4 bg-slate-900/30 border border-slate-900 hover:border-slate-800 rounded-xl transition-all space-y-3 cursor-pointer group"
                          >
                            <div className="flex justify-between items-start">
                              <span className="text-xs font-bold text-indigo-400 font-mono">
                                {call.vapi_call_id ? `${call.vapi_call_id.substring(0, 4)}...${call.vapi_call_id.slice(-4)}` : "N/A"}
                              </span>
                              <span className="text-xs font-bold text-emerald-400">
                                ${(call.cost || 0).toFixed(2)}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                              <div>
                                <span className="text-[9px] text-slate-650 block uppercase font-bold tracking-wider">Asst Phone</span>
                                <span>+1 (984) 371-2375</span>
                              </div>
                              <div>
                                <span className="text-[9px] text-slate-650 block uppercase font-bold tracking-wider">Cust Phone</span>
                                <span>{call.customer?.phone || "N/A"}</span>
                              </div>
                            </div>
                            <div className="flex items-center justify-between pt-2 border-t border-slate-900/60">
                              <div className="flex space-x-1.5">
                                {isOutbound ? (
                                  <span className="inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                    Outbound
                                  </span>
                                ) : (
                                  <span className="inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                    Inbound
                                  </span>
                                )}
                                <span className="inline-flex px-2 py-0.5 rounded-lg text-[9px] font-semibold bg-slate-950 border border-slate-900 text-slate-400 capitalize">
                                  {call.ended_reason ? call.ended_reason.replace("-ended-call", "").replace("-", " ") : "Customer"}
                                </span>
                              </div>
                              <span className="text-[10px] text-slate-500 font-mono">
                                {formatDuration(call.duration)}
                              </span>
                            </div>
                          </div>
                        );
                      });
                    })()}
                  </div>

                  {/* Pagination Controls */}
                  {(() => {
                    const callsList = stats?.recent_calls || [];
                    const sortedCalls = [...callsList].sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                    const filteredCalls = sortedCalls.filter((c: any) => {
                      const searchLower = tableSearch.toLowerCase();
                      const matchCallId = c.vapi_call_id?.toLowerCase().includes(searchLower) || false;
                      const matchAssistant = c.twilio_call_id?.toLowerCase().includes(searchLower) || (c.type === "inboundPhoneCall" && "+19843712375".includes(searchLower)) || false;
                      const matchCustomer = c.customer?.phone?.toLowerCase().includes(searchLower) || false;
                      return matchCallId || matchAssistant || matchCustomer;
                    });
                    const totalPages = Math.ceil(filteredCalls.length / rowsPerPage) || 1;

                    if (filteredCalls.length <= rowsPerPage) return null;

                    return (
                      <div className="flex items-center justify-between pt-4 border-t border-slate-900/60 mt-4 text-[10px] text-slate-500">
                        <span>
                          Showing {(tablePage - 1) * rowsPerPage + 1} to {Math.min(tablePage * rowsPerPage, filteredCalls.length)} of {filteredCalls.length} logs
                        </span>
                        <div className="flex items-center space-x-1">
                          <button
                            disabled={tablePage === 1}
                            onClick={() => setTablePage(prev => Math.max(prev - 1, 1))}
                            className="px-2.5 py-1 bg-slate-950 border border-slate-900 rounded-lg text-slate-400 disabled:opacity-40 hover:text-white transition-all"
                          >
                            Prev
                          </button>
                          <span className="px-2.5 py-0.5 bg-slate-900 border border-slate-850 rounded-lg text-white font-bold font-mono">
                            {tablePage}
                          </span>
                          <button
                            disabled={tablePage === totalPages}
                            onClick={() => setTablePage(prev => Math.min(prev + 1, totalPages))}
                            className="px-2.5 py-1 bg-slate-950 border border-slate-900 rounded-lg text-slate-400 disabled:opacity-40 hover:text-white transition-all"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                <div className="glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col">
                  <h3 className="text-base font-bold text-white mb-6">Upcoming Bookings</h3>
                  <div className="flex-grow space-y-4">
                    {stats?.upcoming_appointments?.map((appt: any) => (
                      <div key={appt.id} className="p-4 rounded-xl bg-slate-900/40 border border-slate-900 hover:border-slate-800 transition-all flex items-start space-x-3.5">
                        <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400 mt-0.5">
                          <Calendar className="w-4.5 h-4.5" />
                        </div>
                        <div className="min-w-0 flex-grow">
                          <h4 className="text-xs font-bold text-white truncate">{appt.title}</h4>
                          <p className="text-[10px] text-slate-400 mt-0.5 truncate">{appt.customer.name}</p>
                          <div className="text-[10px] text-slate-500 font-semibold mt-2.5">
                            {new Date(appt.start_time).toLocaleDateString([], { month: 'short', day: 'numeric' })} at {new Date(appt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : activeTab === "calls" ? (
            // --- VOICE CALL LOGS / OBSERVED CONSOLE ---
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column - List of Call logs */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col space-y-4">
                <div className="flex items-center bg-slate-950 border border-slate-900 px-3.5 py-2 rounded-xl">
                  <Search className="w-4 h-4 text-slate-500 mr-2.5" />
                  <input 
                    type="text" 
                    placeholder="Search callers or phone numbers..."
                    value={searchQuery}
                    onChange={(e) => { setSearchQuery(e.target.value); setCallLogPage(1); }}
                    className="bg-transparent border-0 outline-none text-xs text-slate-300 w-full placeholder-slate-600"
                  />
                </div>
                
                {/* Advanced Filtering Options */}
                <div className="flex gap-2 text-[10px]">
                  <select 
                    value={sentimentFilter} 
                    onChange={(e) => { setSentimentFilter(e.target.value); setCallLogPage(1); }}
                    className="bg-slate-950 border border-slate-900 rounded-xl px-2 py-1.5 text-xs text-slate-400 outline-none w-1/2 cursor-pointer focus:border-indigo-500"
                  >
                    <option value="all">All Sentiments</option>
                    <option value="positive">Positive Sentiment</option>
                    <option value="neutral">Neutral Sentiment</option>
                    <option value="negative">Negative Sentiment</option>
                  </select>
                  <select 
                    value={typeFilter} 
                    onChange={(e) => { setTypeFilter(e.target.value); setCallLogPage(1); }}
                    className="bg-slate-950 border border-slate-900 rounded-xl px-2 py-1.5 text-xs text-slate-400 outline-none w-1/2 cursor-pointer focus:border-indigo-500"
                  >
                    <option value="all">All Directions</option>
                    <option value="outbound">Outbound Calls</option>
                    <option value="inbound">Inbound Calls</option>
                  </select>
                </div>
                
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1 flex-grow">
                  {(() => {
                    const callsList = stats?.recent_calls || [];
                    const filtered = callsList.filter((c: any) => {
                      const matchQuery = c.customer.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.customer.phone.includes(searchQuery);
                      const matchSentiment = sentimentFilter === "all" || c.sentiment === sentimentFilter;
                      const matchType = typeFilter === "all" || (typeFilter === "outbound" ? (c.type === "outboundPhoneCall" || !c.type?.includes("inbound")) : c.type?.includes("inbound"));
                      return matchQuery && matchSentiment && matchType;
                    });
                    
                    const paginated = filtered.slice((callLogPage - 1) * callLogsPerPage, callLogPage * callLogsPerPage);
                    
                    if (paginated.length === 0) {
                      return <p className="text-xs text-slate-500 italic text-center py-8">No call history match.</p>;
                    }
                    
                    return paginated.map((call: any) => (
                      <div 
                        key={call.id} 
                        onClick={() => handleSelectCall(call)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer relative group/row ${
                          selectedCall?.id === call.id 
                            ? "bg-indigo-650/10 border-indigo-500/30" 
                            : "bg-slate-900/30 border-slate-900 hover:border-slate-800"
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-xs font-bold text-white truncate max-w-[130px]">{call.customer.name}</h4>
                            <span className="text-[10px] text-slate-500 block mt-0.5 font-mono">{call.customer.phone}</span>
                          </div>
                          <div className="flex flex-col items-end gap-1.5 shrink-0">
                            <span className="text-[9px] font-semibold text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full font-mono">
                              {formatDuration(call.duration)}
                            </span>
                            <button
                              onClick={async (e) => {
                                e.stopPropagation();
                                const confirmDelete = window.confirm("This will permanently delete this call record from Vocentra database logs.");
                                if (!confirmDelete) return;
                                await handleCallDelete(call.id);
                              }}
                              className="text-rose-500 hover:text-rose-400 p-1 hover:bg-slate-800 rounded transition-all opacity-0 group-hover/row:opacity-100"
                              title="Delete Call Log"
                            >
                              <Trash className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ));
                  })()}
                </div>

                {/* Call Logs Pagination controls */}
                {(() => {
                  const callsList = stats?.recent_calls || [];
                  const filtered = callsList.filter((c: any) => {
                    const matchQuery = c.customer.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.customer.phone.includes(searchQuery);
                    const matchSentiment = sentimentFilter === "all" || c.sentiment === sentimentFilter;
                    const matchType = typeFilter === "all" || (typeFilter === "outbound" ? (c.type === "outboundPhoneCall" || !c.type?.includes("inbound")) : c.type?.includes("inbound"));
                    return matchQuery && matchSentiment && matchType;
                  });
                  const totalP = Math.ceil(filtered.length / callLogsPerPage) || 1;
                  if (filtered.length <= callLogsPerPage) return null;
                  return (
                    <div className="flex items-center justify-between pt-3 border-t border-slate-900/60 mt-2 text-[10px] text-slate-500 font-medium">
                      <span>Showing {(callLogPage-1)*callLogsPerPage + 1} - {Math.min(callLogPage*callLogsPerPage, filtered.length)} of {filtered.length} logs</span>
                      <div className="flex items-center space-x-1">
                        <button disabled={callLogPage === 1} onClick={() => setCallLogPage(prev => Math.max(prev - 1, 1))} className="px-2 py-0.5 bg-slate-950 border border-slate-900 rounded disabled:opacity-40 text-slate-400 hover:text-white transition-all text-[9px]">Prev</button>
                        <span className="px-1.5 font-bold">{callLogPage}</span>
                        <button disabled={callLogPage === totalP} onClick={() => setCallLogPage(prev => Math.min(prev + 1, totalP))} className="px-2 py-0.5 bg-slate-950 border border-slate-900 rounded disabled:opacity-40 text-slate-400 hover:text-white transition-all text-[9px]">Next</button>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Right Column - Call details, searchable Timeline, and Transcript Playback */}
              <div className="lg:col-span-2 space-y-6">
                {selectedCall ? (
                  <div className="glass-panel p-6 rounded-2xl border border-slate-900 space-y-6">
                    <div className="flex justify-between items-start border-b border-slate-900 pb-4">
                      <div>
                        <h3 className="text-base font-bold text-white">{selectedCall.customer.name}</h3>
                        <span className="text-xs text-slate-400">{selectedCall.customer.phone} &bull; {new Date(selectedCall.created_at).toLocaleString()}</span>
                      </div>
                      
                      {/* Audio playback simulator */}
                      <div className="flex items-center space-x-3 bg-slate-900/50 border border-slate-850 px-4 py-1.5 rounded-xl text-xs">
                        <button
                          type="button"
                          onClick={() => {
                            if (!selectedCall.recordingUrl) return;
                            if (audioPlayer.isPlaying) {
                              audioPlayer.pausePlayback();
                            } else {
                              void audioPlayer.playRecording();
                            }
                          }}
                          className="flex items-center gap-1.5 text-emerald-400 shrink-0"
                        >
                          {audioPlayer.isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </button>
                        <span className="font-mono text-slate-300">{formatDuration(selectedCall.duration)}</span>
                        <span className="text-slate-500">|</span>
                        <span className="font-semibold text-indigo-400">${selectedCall.cost.toFixed(3)}</span>
                      </div>
                    </div>

                    {/* Lead Details & Outbound Dial button */}
                    {selectedCall.status !== "ongoing" ? (
                      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-900 flex flex-col gap-3">
                        <div className="flex justify-between items-start">
                          <div className="space-y-1">
                            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Lead Outbound Dialer</span>
                            <div className="text-xs text-slate-400">
                              Assistant: <span className="font-mono text-indigo-400 font-bold">{vapiId || "vapi_assistant_mock_id"}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-2 items-center w-full">
                          <div className="relative w-full sm:flex-grow">
                            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500 text-xs font-semibold">To:</span>
                            <input 
                              type="text" 
                              value={dialNumber} 
                              onChange={(e) => setDialNumber(e.target.value)}
                              className="w-full pl-9 pr-4 py-2 bg-slate-900/60 border border-slate-850 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                              placeholder="+19843712375"
                            />
                          </div>
                          <button 
                            onClick={() => handleTriggerOutboundCall(dialNumber, selectedCall.customer.name)}
                            className="w-full sm:w-auto px-5 py-2 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-xs font-bold text-white rounded-xl transition-all flex items-center justify-center space-x-1.5 shrink-0 shadow-lg shadow-emerald-950/20"
                          >
                            <Phone className="w-3.5 h-3.5" />
                            <span>Call Now</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-rose-950/10 border border-rose-900/30 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                        <div className="space-y-1 flex items-center space-x-3">
                          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                          {/* AI Holographic Orb */}
                          <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-indigo-500 via-purple-500 to-cyan-400 animate-holographic-orb relative shadow-[0_0_15px_rgba(99,102,241,0.5)] shrink-0">
                            <div className="absolute inset-0.5 rounded-full bg-slate-950/70 backdrop-blur-xs flex items-center justify-center">
                              <div className="w-1.5 h-1.5 rounded-full bg-cyan-450 animate-ping opacity-80"></div>
                            </div>
                          </div>
                          <div>
                            <span className="text-[10px] text-rose-400 uppercase font-bold tracking-wider block">Outbound Call Active</span>
                            <span className="text-xs text-slate-400 block">Agent is communicating with lead...</span>
                          </div>
                        </div>
                        <button 
                          onClick={() => handleEndActiveCall(selectedCall.vapi_call_id)}
                          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-xs font-bold text-white rounded-xl transition-all flex items-center space-x-1.5"
                        >
                          <PhoneOff className="w-3.5 h-3.5" />
                          <span>End Call</span>
                        </button>
                      </div>
                    )}

                    {/* Timeline flow */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Call Event Timeline</h4>
                      <div className="relative pl-6 border-l border-indigo-500/20 space-y-5">
                        <div className="relative">
                          <CheckCircle2 className="w-4 h-4 text-indigo-500 bg-[#020617] absolute -left-[30px] top-0" />
                          <h5 className="text-xs font-semibold text-white">Call Initiated</h5>
                          <span className="text-[9px] text-slate-500 block">Establish handshake connection</span>
                        </div>
                        <div className="relative">
                          <CheckCircle2 className="w-4 h-4 text-indigo-500 bg-[#020617] absolute -left-[30px] top-0" />
                          <h5 className="text-xs font-semibold text-white">AI Greeting Prompt Assembled</h5>
                          <span className="text-[9px] text-slate-500 block">System prompt qualified & dispatched</span>
                        </div>
                        <div className="relative">
                          <CheckCircle2 className="w-4 h-4 text-indigo-500 bg-[#020617] absolute -left-[30px] top-0" />
                          <h5 className="text-xs font-semibold text-white">Customer Intent Identified</h5>
                          <span className="text-[9px] text-slate-500 block">Detected intent parameters: Booking Slot</span>
                        </div>
                        {selectedCall.lead_score >= 80 && (
                          <div className="relative">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 bg-[#020617] absolute -left-[30px] top-0" />
                            <h5 className="text-xs font-semibold text-white">CRM Qualified & n8n webhook triggered</h5>
                            <span className="text-[9px] text-slate-500 block">Lead qualifiers parsed (HubSpot deal sync complete)</span>
                          </div>
                        )}
                        <div className="relative">
                          <CheckCircle2 className="w-4 h-4 text-indigo-500 bg-[#020617] absolute -left-[30px] top-0" />
                          <h5 className="text-xs font-semibold text-white">Call Finalized</h5>
                          <span className="text-[9px] text-slate-500 block">Completed sentiment: {selectedCall.sentiment}</span>
                        </div>
                      </div>
                    </div>

                    {/* Summary and Searchable Transcript */}
                    <div className="space-y-4 pt-4 border-t border-slate-900">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Voice Conversation Details</h4>
                        {detailLoading && <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin" />}
                      </div>

                      {detailError ? (
                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-300">
                          <div className="font-semibold">Unable to retrieve call details.</div>
                          <button
                            onClick={() => handleSelectCall(selectedCall)}
                            className="mt-2 text-xs font-semibold text-amber-200 underline"
                          >
                            Retry
                          </button>
                        </div>
                      ) : null}

                      {selectedCall.recordingUrl ? (
                        <div className="rounded-xl border border-slate-900 bg-slate-950/50 p-4">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Recording</h4>
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => {
                                  if (audioPlayer.isPlaying) {
                                    audioPlayer.pausePlayback();
                                  } else {
                                    void audioPlayer.playRecording();
                                  }
                                }}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm font-semibold text-white"
                              >
                                {audioPlayer.isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : audioPlayer.isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                              </button>
                              <button
                                type="button"
                                onClick={() => audioPlayer.replay()}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm font-semibold text-white"
                              >
                                Replay
                              </button>
                              <div className="flex-1 text-xs text-slate-400">
                                {audioPlayer.isLoading ? "Loading recording..." : audioPlayer.error || "Ready to play"}
                              </div>
                              {audioPlayer.error ? (
                                <button
                                  type="button"
                                  onClick={() => void audioPlayer.playRecording()}
                                  className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm font-semibold text-white"
                                >
                                  Retry
                                </button>
                              ) : null}
                            </div>
                            <input
                              type="range"
                              min={0}
                              max={audioPlayer.duration || 0}
                              step={0.1}
                              value={audioPlayer.currentTime}
                              onChange={(event) => audioPlayer.seekTo(Number(event.target.value))}
                              className="w-full accent-indigo-500"
                            />
                            <div className="flex items-center justify-between text-[11px] text-slate-400">
                              <span>{formatDuration(Math.floor(audioPlayer.currentTime))}</span>
                              <span>{formatDuration(Math.floor(audioPlayer.duration))}</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-slate-300">
                              <label className="text-[11px] uppercase tracking-wider text-slate-500">Speed</label>
                              <select
                                value={audioPlayer.playbackRate}
                                onChange={(event) => audioPlayer.setPlaybackRate(Number(event.target.value))}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-2 py-1"
                              >
                                {[0.5, 1, 1.25, 1.5, 2].map((rate) => (
                                  <option key={rate} value={rate}>{rate}x</option>
                                ))}
                              </select>
                              <button
                                type="button"
                                onClick={() => audioPlayer.toggleMute()}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-2 py-1"
                              >
                                {audioPlayer.isMuted ? "Unmute" : "Mute"}
                              </button>
                              <input
                                type="range"
                                min={0}
                                max={1}
                                step={0.05}
                                value={audioPlayer.volume}
                                onChange={(event) => audioPlayer.setVolume(Number(event.target.value))}
                                className="w-24 accent-indigo-500"
                              />
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-xl border border-slate-900 bg-slate-950/50 p-4 text-sm text-slate-400">
                          No recording available.
                        </div>
                      )}

                      <div className="space-y-3 max-h-[320px] overflow-y-auto bg-slate-950 p-4 rounded-xl border border-slate-900">
                        {selectedCall.status === "ongoing" ? (
                          liveTranscript.length > 0 ? (
                            liveTranscript.map((msg: any, idx: number) => (
                              <div key={idx} className={`p-2.5 rounded-lg text-xs leading-relaxed max-w-[80%] ${
                                msg.role === "user" 
                                  ? "bg-indigo-650/10 border border-indigo-500/20 text-indigo-300 ml-auto" 
                                  : "bg-slate-900/60 border border-slate-800 text-slate-200"
                              }`}>
                                <span className="font-bold block mb-1 text-[9px] uppercase tracking-wider text-slate-500">
                                  {msg.role === "user" ? "Customer" : "Vocentra AI"}
                                </span>
                                {msg.content}
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-slate-500 italic">Waiting for utterances... Speak into your microphone.</p>
                          )
                        ) : (
                          selectedCall.messages && selectedCall.messages.length > 0 ? (
                            selectedCall.messages.map((msg: any) => (
                              <div key={msg.id} className={`p-2.5 rounded-lg text-xs leading-relaxed max-w-[80%] ${
                                msg.role === "user" 
                                  ? "bg-indigo-650/10 border border-indigo-500/20 text-indigo-300 ml-auto" 
                                  : "bg-slate-900/60 border border-slate-800 text-slate-200"
                              }`}>
                                <span className="font-bold block mb-1 text-[9px] uppercase tracking-wider text-slate-500">
                                  {getSpeakerLabel(msg)}
                                </span>
                                <div className="text-[10px] text-slate-500 mb-1">{msg.created_at || ""}</div>
                                {msg.content}
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-slate-500 italic">No conversation logs stored for this completed call.</p>
                          )
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="rounded-xl border border-slate-900 bg-slate-950/50 p-4">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Summary</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {selectedCall.summary || "No summary available."}
                          </p>
                        </div>
                        <div className="rounded-xl border border-slate-900 bg-slate-950/50 p-4">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Analytics</h4>
                          <div className="space-y-2 text-xs text-slate-300">
                            <div className="flex justify-between"><span>Duration</span><span>{formatDuration(selectedCall.duration || 0)}</span></div>
                            <div className="flex justify-between"><span>Cost</span><span>{formatCurrency(selectedCall.cost)}</span></div>
                            <div className="flex justify-between"><span>Ended Reason</span><span>{selectedCall.endedReason || selectedCall.ended_reason || "N/A"}</span></div>
                            <div className="flex justify-between"><span>Model</span><span>{selectedCall.model || "N/A"}</span></div>
                            <div className="flex justify-between"><span>Voice</span><span>{selectedCall.voice || "N/A"}</span></div>
                            <div className="flex justify-between"><span>Provider</span><span>{selectedCall.provider || "N/A"}</span></div>
                            {selectedCall.latencyMetrics && Object.keys(selectedCall.latencyMetrics).length > 0 ? (
                              <div className="pt-2 border-t border-slate-900">
                                {Object.entries(selectedCall.latencyMetrics).map(([key, value]) => (
                                  <div key={key} className="flex justify-between"><span>{key}</span><span>{String(value)}</span></div>
                                ))}
                              </div>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="glass-panel p-10 rounded-2xl border border-slate-900 text-center">
                    <Phone className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                    <h4 className="text-sm font-bold text-white">No Call Selected</h4>
                    <p className="text-xs text-slate-500 mt-1">Select a call log on the left side to review logs, transcripts, and event bus timelines.</p>
                  </div>
                )}
              </div>
            </div>
          ) : activeTab === "knowledge" ? (
            // --- KNOWLEDGE BASE TAB ---
            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden flex flex-col space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-base font-bold text-white">Vector Knowledge Base</h3>
                    <p className="text-xs text-slate-500">Inject PDFs and text documents. Query uses cosine similarity parameters to inject contexts.</p>
                  </div>
                  <div>
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      onChange={handleFileUpload} 
                      className="hidden" 
                      accept=".txt,.pdf,.json"
                    />
                    <button 
                      onClick={() => fileInputRef.current?.click()}
                      className="py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white rounded-xl flex items-center space-x-1.5 transition-all"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Upload Document</span>
                    </button>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-900">
                  {documents.length > 0 ? (
                    documents.map((doc) => (
                      <div key={doc.id} className="p-4 bg-slate-950 border border-slate-900 rounded-xl relative overflow-hidden group">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-xs font-bold text-white truncate max-w-[80%]">{doc.title}</h4>
                          <span className="text-[9px] uppercase font-bold text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">
                            {doc.content_type}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 line-clamp-3 leading-relaxed">
                          {doc.text_preview || doc.text_content}
                        </p>
                        <span className="text-[9px] text-slate-600 block mt-3">
                          Uploaded: {new Date(doc.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="col-span-2 text-center py-8">
                      <p className="text-xs text-slate-500 italic">No files uploaded. Click "Upload Document" to add reference material.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : activeTab === "team" ? (
            // --- TEAM MEMBERS & AUDIT LOGS TAB ---
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column: Team lists & invite member */}
              <div className="lg:col-span-2 space-y-6">
                <div className="glass-panel p-6 rounded-2xl border border-slate-900 space-y-4">
                  <h3 className="text-base font-bold text-white">Active Team Members</h3>
                  
                  <div className="space-y-3">
                    {teamMembers.map((m) => (
                      <div key={m.id} className="p-4 bg-slate-950/60 rounded-xl border border-slate-900 flex justify-between items-center">
                        <div>
                          <h4 className="text-xs font-bold text-white">{m.name}</h4>
                          <span className="text-[10px] text-slate-500 block mt-0.5">{m.email}</span>
                        </div>
                        <span className="text-[10px] uppercase font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                          {m.role}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Invite Colleague Form */}
                <div className="glass-panel p-6 rounded-2xl border border-slate-900 space-y-4">
                  <h3 className="text-base font-bold text-white">Invite Team Colleague</h3>
                  <form onSubmit={handleInviteMember} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <input 
                      type="text" 
                      placeholder="Name" 
                      value={inviteName}
                      onChange={(e) => setInviteName(e.target.value)}
                      className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                      required
                    />
                    <input 
                      type="email" 
                      placeholder="Email" 
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                      required
                    />
                    <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white px-4 py-2 rounded-xl transition-all w-full">
                      Send Invitation
                    </button>
                  </form>
                </div>
              </div>

              {/* Right Column: Audit Logs list */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col space-y-4">
                <h3 className="text-base font-bold text-white">SaaS Audit Logs</h3>
                <div className="space-y-4 pr-1 max-h-[480px] overflow-y-auto">
                  {auditLogs.map((log) => (
                    <div key={log.id} className="p-3 bg-slate-900/30 border border-slate-900 rounded-lg space-y-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="font-bold text-indigo-400 capitalize">{log.action.replace("_", " ")}</span>
                        <span className="text-slate-500">{new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <p className="text-xs text-slate-300">{log.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : activeTab === "billing" ? (
            // --- BILLING & QUOTAS TAB ---
            <div className="space-y-8">
              {/* Quota limit cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Usage Quota Meter</h4>
                  <div className="flex justify-between items-baseline mb-4">
                    <span className="text-2xl font-extrabold text-white">{usageCount} / {usageLimit}</span>
                    <span className="text-xs text-slate-500">Calls counted this month</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${Math.min(100, (usageCount / usageLimit) * 100)}%` }}></div>
                  </div>
                </div>

                <div className="glass-panel p-6 rounded-2xl border border-slate-900 relative overflow-hidden">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Active Plan</h4>
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="text-lg font-bold text-white block capitalize">{billingTier} Tier</span>
                      <span className="text-[10px] text-slate-500">Renewal scheduled: August 01, 2026</span>
                    </div>
                    <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full uppercase">{billingTier}</span>
                  </div>
                </div>
              </div>

              {/* Pricing comparison list */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-900 space-y-4">
                <h3 className="text-base font-bold text-white mb-4">Upgrade Subscription Plans</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-xl flex flex-col justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 uppercase">Starter Plan</h4>
                      <span className="text-xl font-bold text-white mt-2 block">$0 / mo</span>
                      <p className="text-[11px] text-slate-500 mt-2">Up to 100 voice calls/month. Shared prompt libraries. cosine search metrics.</p>
                    </div>
                    <button 
                      onClick={() => handleUpgradeBilling("free")}
                      className={`mt-6 w-full py-2 text-xs font-semibold rounded-lg transition-all border ${
                        billingTier === "free" 
                          ? "bg-slate-900 text-slate-400 border-slate-850 cursor-default" 
                          : "bg-indigo-600 hover:bg-indigo-500 text-white border-transparent"
                      }`}
                    >
                      {billingTier === "free" ? "Active Free" : "Downgrade to Starter"}
                    </button>
                  </div>
                  
                  <div className="p-4 bg-indigo-950/10 border border-indigo-500/20 rounded-xl flex flex-col justify-between relative">
                    <span className="absolute -top-2.5 right-4 text-[9px] font-extrabold uppercase bg-indigo-600 text-white px-2 py-0.5 rounded-full">POPULAR</span>
                    <div>
                      <h4 className="text-xs font-bold text-indigo-400 uppercase">Growth Plan</h4>
                      <span className="text-xl font-bold text-white mt-2 block">$199 / mo</span>
                      <p className="text-[11px] text-slate-400 mt-2">Up to 1000 voice calls/month. HubSpot sync workflows, customized settings panels, 24/7 support.</p>
                    </div>
                    <button 
                      onClick={() => handleUpgradeBilling("growth")}
                      className={`mt-6 w-full py-2 text-xs font-semibold rounded-lg transition-all ${
                        billingTier === "growth" 
                          ? "bg-indigo-950 text-indigo-400 border border-indigo-500/20 cursor-default" 
                          : "bg-indigo-600 hover:bg-indigo-500 text-white"
                      }`}
                    >
                      {billingTier === "growth" ? "Active Growth" : "Upgrade to Growth"}
                    </button>
                  </div>

                  <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-xl flex flex-col justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 uppercase">Enterprise Plan</h4>
                      <span className="text-xl font-bold text-white mt-2 block">Custom / mo</span>
                      <p className="text-[11px] text-slate-500 mt-2">Unlimited calls. Dedicated pgvector nodes. Custom n8n webhook routes, audit logs, SLA guarantees.</p>
                    </div>
                    <button 
                      onClick={() => handleUpgradeBilling("enterprise")}
                      className={`mt-6 w-full py-2 text-xs font-semibold rounded-lg transition-all border ${
                        billingTier === "enterprise" 
                          ? "bg-indigo-950 text-indigo-400 border border-indigo-500/20 cursor-default" 
                          : "bg-indigo-600 hover:bg-indigo-500 text-white"
                      }`}
                    >
                      {billingTier === "enterprise" ? "Active Enterprise" : "Upgrade to Enterprise"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : activeTab === "health" ? (
            // --- HEALTH DIAGNOSTICS TAB ---
            <div className="space-y-6">
              {/* Overall status header card */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-900 flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-emerald-500/10 border border-emerald-500/20">
                    <ShieldAlert className="w-6 h-6 text-emerald-400 animate-pulse" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">System Operations Diagnostics</h3>
                    <p className="text-xs text-slate-400">Telemetry links checking microservices and third-party voice providers.</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <button 
                    onClick={fetchHealthStatus}
                    className="p-2 border border-slate-850 hover:bg-slate-900 rounded-lg text-slate-400 hover:text-white transition-all flex items-center space-x-1.5 text-xs font-semibold"
                    disabled={healthLoading}
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? "animate-spin" : ""}`} />
                    <span>Diagnostics Run</span>
                  </button>
                  <div className="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3.5 py-1.5 rounded-full flex items-center space-x-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                    <span>System Healthy</span>
                  </div>
                </div>
              </div>

              {/* Status Grid */}
              {healthData ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Database Card */}
                  <div className="glass-panel p-5 rounded-2xl border border-slate-900 space-y-4">
                    <div className="flex justify-between items-start">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">PostgreSQL Database</h4>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        healthData.database.status === "healthy"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}>
                        {healthData.database.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-2xl font-extrabold text-white">{healthData.database.latency_ms}ms</span>
                      <span className="text-[10px] text-slate-500 block">SQL Query roundtrip latency</span>
                    </div>
                  </div>

                  {/* Redis Card */}
                  <div className="glass-panel p-5 rounded-2xl border border-slate-900 space-y-4">
                    <div className="flex justify-between items-start">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Redis Message Queue</h4>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        healthData.redis.status === "healthy"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}>
                        {healthData.redis.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-2xl font-extrabold text-white">{healthData.redis.latency_ms}ms</span>
                      <span className="text-[10px] text-slate-500 block">arq worker pool sync ping</span>
                    </div>
                  </div>

                  {/* Vapi Card */}
                  <div className="glass-panel p-5 rounded-2xl border border-slate-900 space-y-4">
                    <div className="flex justify-between items-start">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Vapi Voice Pipeline</h4>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        healthData.vapi.status === "healthy"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}>
                        {healthData.vapi.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-2xl font-extrabold text-white">{healthData.vapi.latency_ms}ms</span>
                      <span className="text-[10px] text-slate-500 block">API handshake & credentials check</span>
                    </div>
                  </div>

                  {/* Twilio Card */}
                  <div className="glass-panel p-5 rounded-2xl border border-slate-900 space-y-4">
                    <div className="flex justify-between items-start">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Twilio Telephony</h4>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        healthData.twilio.status === "healthy"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}>
                        {healthData.twilio.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-xl font-bold text-white block">
                        {healthData.twilio.status === "healthy" ? "Account Authorized" : "Unconfigured / Invalid"}
                      </span>
                      <span className="text-[10px] text-slate-500 block">SIP Trunking / Inbound routes active</span>
                    </div>
                  </div>

                  {/* WebSockets Card */}
                  <div className="glass-panel p-5 rounded-2xl border border-slate-900 space-y-4">
                    <div className="flex justify-between items-start">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">WebSocket Listeners</h4>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        healthData.websockets.clients_count > 0
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-slate-900 text-slate-400 border-slate-800"
                      }`}>
                        {healthData.websockets.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-2xl font-extrabold text-white">{healthData.websockets.clients_count} Clients</span>
                      <span className="text-[10px] text-slate-500 block">Active dashboard streaming slots</span>
                    </div>
                  </div>

                  {/* RAG Knowledge Store Card */}
                  <div className="glass-panel p-5 rounded-2xl border border-slate-900 space-y-4">
                    <div className="flex justify-between items-start">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Vector Store chunks</h4>
                      <span className="inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        PGVECTOR
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-2xl font-extrabold text-white">{healthData.knowledge_base.document_count} files</span>
                      <span className="text-[10px] text-slate-500 block">Ingested reference docs in DB</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="min-h-[200px] flex items-center justify-center">
                  <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
                </div>
              )}
            </div>
          ) : (
            // --- SETTINGS CONSOLE TAB ---
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-slate-900 space-y-4">
                <h3 className="text-base font-bold text-white">SaaS Configuration Control</h3>
                <p className="text-xs text-slate-500">Configure Twilio credentials and n8n webhooks to synchronize voice pipeline triggers multi-tenant.</p>
                
                <div className="space-y-4 pt-4 border-t border-slate-900">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] text-slate-500 font-bold uppercase block">Twilio Account SID</label>
                      <input 
                        type="text" 
                        placeholder="ACxxxxxxxxxxxxxxxx"
                        value={twilioSid}
                        onChange={(e) => setTwilioSid(e.target.value)}
                        className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] text-slate-500 font-bold uppercase block">Twilio Auth Token</label>
                      <input 
                        type="password" 
                        placeholder="••••••••••••••••"
                        value={twilioToken}
                        onChange={(e) => setTwilioToken(e.target.value)}
                        className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] text-slate-500 font-bold uppercase block">Vapi Assistant Reference ID</label>
                    <input 
                      type="text" 
                      placeholder="vapi-assistant-uuid"
                      value={vapiId}
                      onChange={(e) => setVapiId(e.target.value)}
                      className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] text-slate-500 font-bold uppercase block">Sequential Call Delay (Seconds)</label>
                    <input 
                      type="number" 
                      placeholder="30"
                      value={callDelay}
                      onChange={(e) => setCallDelay(Number(e.target.value))}
                      className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] text-slate-500 font-bold uppercase block">Primary n8n Automation Webhook</label>
                    <input 
                      type="text" 
                      placeholder="https://n8n.yourdomain.com/webhook/..."
                      value={n8nUrl}
                      onChange={(e) => setN8nUrl(e.target.value)}
                      className="bg-slate-950 border border-slate-900 rounded-xl px-3.5 py-2 text-xs outline-none text-slate-300 w-full"
                    />
                  </div>

                  <button 
                    onClick={handleSaveSettings}
                    className="py-2.5 px-6 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white rounded-xl transition-all block w-full mt-6"
                  >
                    Save Configuration Settings
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

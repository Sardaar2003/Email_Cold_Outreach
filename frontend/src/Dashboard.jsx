import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Send, 
  MessageSquare, 
  Clock, 
  Upload, 
  Play, 
  Square, 
  Settings,
  BarChart3,
  Mail,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Timer,
  FileText
} from 'lucide-react';
import api from './api';

const Dashboard = () => {
  const [leads, setLeads] = useState([]);
  const [analytics, setAnalytics] = useState({
    total_leads: 0,
    sent: 0,
    replied: 0,
    pending: 0,
    sent_this_week: 0
  });
  const [isCampaignRunning, setIsCampaignRunning] = useState(false);
  const [campaignStatus, setCampaignStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [sendingReport, setSendingReport] = useState(false);
  const [productDesc, setProductDesc] = useState('');
  const [reportEmail, setReportEmail] = useState('');
  const [weeklyLimit, setWeeklyLimit] = useState(20);
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    fetchConfig();
    fetchData();
    const interval = setInterval(fetchData, 15000); // Poll every 15 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!campaignStatus?.next_run_time || !campaignStatus?.is_running) {
      setTimeLeft('');
      return;
    }
    
    const calculateTimeLeft = () => {
      const nextRun = new Date(campaignStatus.next_run_time).getTime();
      const now = new Date().getTime();
      const difference = nextRun - now;
      
      if (difference <= 0) {
        setTimeLeft('Running soon...');
        return;
      }
      
      const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((difference % (1000 * 60)) / 1000);
      
      setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
    };

    calculateTimeLeft();
    const timer = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(timer);
  }, [campaignStatus?.next_run_time, campaignStatus?.is_running]);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/configs');
      const configs = res.data;
      if (configs.product_description) setProductDesc(configs.product_description);
      if (configs.REPORT_RECEIVER_EMAIL) setReportEmail(configs.REPORT_RECEIVER_EMAIL);
      if (configs.weekly_email_limit) setWeeklyLimit(parseInt(configs.weekly_email_limit, 10));
    } catch (err) {
      console.error("Error fetching configs:", err);
    }
  };

  const fetchData = async () => {
    try {
      const [leadsRes, analyticsRes, statusRes] = await Promise.all([
        api.get('/leads'),
        api.get('/analytics'),
        api.get('/campaign-status')
      ]);
      setLeads(leadsRes.data);
      setAnalytics(analyticsRes.data);
      setCampaignStatus(statusRes.data);
      setIsCampaignRunning(statusRes.data.is_running);
    } catch (err) {
      console.error("Error fetching data:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    try {
      await api.post('/upload-leads', formData);
      fetchData();
    } catch (err) {
      alert("Upload failed: " + err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
    }
  };

  const toggleCampaign = async () => {
    try {
      if (isCampaignRunning) {
        await api.post('/stop-campaign');
      } else {
        await api.post('/start-campaign');
      }
      setIsCampaignRunning(!isCampaignRunning);
      fetchData(); // immediately fetch new status and next run time
    } catch (err) {
      alert("Failed to toggle campaign");
    }
  };

  const resetCampaign = async () => {
    if (!window.confirm("Are you sure you want to reset the campaign? This will clear email logs and set all leads to Pending.")) return;
    
    setResetting(true);
    try {
      await api.post('/reset-campaign');
      fetchData();
      alert("Campaign reset successfully");
    } catch (err) {
      alert("Reset failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setResetting(false);
    }
  };

  const syncReplies = async () => {
    setSyncing(true);
    try {
      await api.post('/sync-replies');
      fetchData(); // pull new response statuses
      alert("Replies successfully synced via IMAP!");
    } catch (err) {
      alert("Failed to sync replies: " + (err.response?.data?.detail || err.message));
    } finally {
      setSyncing(false);
    }
  };

  const testReport = async () => {
    setSendingReport(true);
    try {
      await api.post('/test-report');
      alert("Daily summary report generated and sent to your email!");
    } catch (err) {
      alert("Failed to send report: " + (err.response?.data?.detail || err.message));
    } finally {
      setSendingReport(false);
    }
  };

  const updateConfig = async (key, value) => {
    try {
      await api.post(`/configure`, { key: key.toString(), value: value.toString() });
      alert("Configuration updated");
    } catch (err) {
      alert("Update failed");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">AI SDR Dashboard</h1>
            <p className="text-slate-500 mt-1">Manage your automated sales outreach</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="cursor-pointer bg-white px-4 py-2 border border-slate-200 rounded-xl hover:bg-slate-50 transition-all flex items-center gap-2 text-sm font-medium shadow-sm">
              <Upload size={18} className="text-primary-600" />
              <span>{uploading ? "Uploading..." : "Import Leads"}</span>
              <input type="file" className="hidden" onChange={handleFileUpload} accept=".xlsx,.xls" />
            </label>
            <button 
              onClick={syncReplies}
              disabled={syncing}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-semibold transition-all shadow-md bg-white border border-slate-200 text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 disabled:opacity-50`}
            >
              <RefreshCw size={18} className={syncing ? "animate-spin text-indigo-500" : "text-indigo-500"} />
              {syncing ? "Syncing..." : "Sync Replies"}
            </button>
            <button 
              onClick={testReport}
              disabled={sendingReport}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-semibold transition-all shadow-md bg-white border border-slate-200 text-slate-700 hover:bg-amber-50 hover:text-amber-600 hover:border-amber-200 disabled:opacity-50`}
            >
              <FileText size={18} className="text-amber-500" />
              {sendingReport ? "Sending..." : "Test Report"}
            </button>
            <button 
              onClick={resetCampaign}
              disabled={resetting}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-semibold transition-all shadow-md bg-white border border-slate-200 text-slate-700 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 disabled:opacity-50`}
            >
              <RefreshCw size={18} className={resetting ? "animate-spin" : ""} />
              {resetting ? "Resetting..." : "Reset"}
            </button>
            <button 
              onClick={toggleCampaign}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-semibold transition-all shadow-md ${
                isCampaignRunning 
                ? 'bg-rose-500 text-white hover:bg-rose-600' 
                : 'bg-emerald-500 text-white hover:bg-emerald-600'
              }`}
            >
              {isCampaignRunning ? <Square size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
              {isCampaignRunning ? "Stop Campaign" : "Start Campaign"}
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard icon={<Users className="text-blue-500" />} label="Total Leads" value={analytics.total_leads} />
          <StatCard icon={<Send className="text-indigo-500" />} label="Emails Sent" value={analytics.sent} />
          <StatCard icon={<MessageSquare className="text-emerald-500" />} label="Responses" value={analytics.replied} />
          <StatCard icon={<Clock className="text-amber-500" />} label="Weekly Limit" value={`${analytics.sent_this_week} / ${weeklyLimit}`} />
        </div>

        {/* Campaign Status Banner */}
        {campaignStatus && (
          <div className="bg-indigo-50/80 border border-indigo-100 p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between shadow-sm gap-4">
            <div className="flex items-center gap-3">
              <div className="relative flex h-3 w-3">
                {campaignStatus.is_running && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                <span className={`relative inline-flex rounded-full h-3 w-3 ${campaignStatus.is_running ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-indigo-950">
                  {campaignStatus.is_running ? 'Campaign is Active' : 'Campaign is Paused'}
                </span>
                <span className="text-xs text-indigo-700/80 mt-0.5 font-medium">
                  Last sent: {campaignStatus.last_email_sent_to ? (
                    <>
                      <span className="text-indigo-900 mx-1">{campaignStatus.last_email_sent_to}</span> 
                      {campaignStatus.last_email_sent_at && `(${new Date(campaignStatus.last_email_sent_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})})`}
                    </>
                  ) : 'None'}
                </span>
              </div>
            </div>
            
            {campaignStatus.is_running && campaignStatus.next_run_time && (
              <div className="flex items-center gap-2 bg-white/60 px-4 py-2 rounded-lg border border-indigo-100 shadow-sm text-sm">
                <Timer size={16} className="text-indigo-500" />
                <span className="text-indigo-900 font-medium tracking-tight">Next email in:</span>
                <span className="text-amber-600 font-bold font-mono text-[13px]">{timeLeft || 'Calculating...'}</span>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Leads Table */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                <h2 className="font-semibold text-slate-800">Lead Registry</h2>
                <div className="text-xs text-slate-400 font-medium">RECENTLY ADDED</div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4">Name</th>
                      <th className="px-6 py-4">Company</th>
                      <th className="px-6 py-4">Industry</th>
                      <th className="px-6 py-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {leads.map((lead) => (
                      <tr key={lead.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 font-medium text-slate-900">{lead.first_name} {lead.last_name}</td>
                        <td className="px-6 py-4 text-slate-600">{lead.company_name}</td>
                        <td className="px-6 py-4 text-slate-500">{lead.industry}</td>
                        <td className="px-6 py-4">
                          <StatusBadge status={lead.status} category={lead.response_category} />
                        </td>
                      </tr>
                    ))}
                    {leads.length === 0 && (
                      <tr>
                        <td colSpan="4" className="px-6 py-10 text-center text-slate-400">No leads found. Upload an Excel file to get started.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Configuration Sidebar */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
                <Settings size={20} className="text-slate-400" />
                <h2 className="font-semibold text-slate-800">Campaign Settings</h2>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Product Description</label>
                  <textarea 
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none transition-all resize-none h-32"
                    placeholder="Describe what you are selling..."
                    value={productDesc}
                    onChange={(e) => setProductDesc(e.target.value)}
                  />
                  <button 
                    onClick={() => updateConfig('product_description', productDesc)}
                    className="mt-2 w-full text-xs font-semibold py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    Save Description
                  </button>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Daily Report Email</label>
                  <input 
                    type="email"
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none transition-all"
                    placeholder="receiver@example.com"
                    value={reportEmail}
                    onChange={(e) => setReportEmail(e.target.value)}
                  />
                  <button 
                    onClick={() => updateConfig('REPORT_RECEIVER_EMAIL', reportEmail)}
                    className="mt-2 w-full text-xs font-semibold py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    Save Email
                  </button>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Weekly Email Limit</label>
                    <span className="text-sm font-bold text-primary-600 bg-primary-50 px-2 py-0.5 rounded-md">{weeklyLimit}</span>
                  </div>
                  <input 
                    type="range" 
                    min="1" 
                    max="100" 
                    value={weeklyLimit} 
                    onChange={(e) => setWeeklyLimit(e.target.value)}
                    onMouseUp={() => updateConfig('weekly_email_limit', weeklyLimit)}
                    className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-primary-600"
                  />
                  <p className="text-[10px] text-slate-400 mt-2">Maximum emails the system will send per week to maintain deliverability.</p>
                </div>
              </div>
            </div>

            {/* AI Insights Card */}
            <div className="bg-gradient-to-br from-primary-600 to-indigo-700 p-6 rounded-2xl text-white shadow-lg space-y-4">
              <div className="flex items-center gap-2">
                <BarChart3 size={20} />
                <h2 className="font-semibold">AI Assistant Tips</h2>
              </div>
              <p className="text-sm text-primary-100 leading-relaxed">
                Personalized emails generally see a 3x higher response rate. Your current GPT-4o integration is optimizing for industry specific value props.
              </p>
              <div className="pt-2">
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full font-medium">Tip: Use niche industry descriptions</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon, label, value }) => (
  <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
    <div className="p-3 bg-slate-50 rounded-xl">
      {icon}
    </div>
    <div>
      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
    </div>
  </div>
);

const StatusBadge = ({ status, category }) => {
  const getColors = () => {
    if (status === 'Replied') {
      if (category === 'Interested') return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      if (category === 'Not Interested') return 'bg-rose-100 text-rose-700 border-rose-200';
      return 'bg-amber-100 text-amber-700 border-amber-200';
    }
    if (status === 'Email Sent') return 'bg-blue-100 text-blue-700 border-blue-200';
    if (status === 'Processing') return 'bg-indigo-100 text-indigo-700 border-indigo-200 animate-pulse';
    if (status === 'Drafted') return 'bg-purple-100 text-purple-700 border-purple-200';
    if (status === 'Failed') return 'bg-red-100 text-red-700 border-red-200 font-bold';
    return 'bg-slate-100 text-slate-500 border-slate-200';
  };

  return (
    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-tight border ${getColors()}`}>
      {status === 'Replied' ? `${status}: ${category}` : status}
    </span>
  );
};

export default Dashboard;

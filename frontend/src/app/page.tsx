"use client";

import { useState } from 'react';
import axios from 'axios';
import TradeEvaluationForm from '@/components/TradeEvaluationForm';
import DecisionReport from '@/components/DecisionReport';
import { ArrowLeft } from 'lucide-react';

export default function Home() {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAudit = async (data: any) => {
    setLoading(true);
    try {
      // Connect to backend API
      const response = await axios.post('https://web-production-2c287.up.railway.app/api/v1/audit', data);
      
      // Artificial delay to simulate "Calculating..." [cite: 361]
      setTimeout(() => {
        setReport(response.data);
        setLoading(false);
      }, 1500);
      
    } catch (error) {
      console.error("Audit failed", error);
      alert("Failed to connect to the Risk Engine. Is the backend running?");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-gray-100 p-6 md:p-12 font-sans">
      
      {/* Navbar */}
      <nav className="flex justify-between items-center max-w-5xl mx-auto mb-12">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-teal-500 rounded-full animate-pulse" />
          <span className="font-bold text-lg tracking-tight">RiskGuard<span className="text-gray-600">.ai</span></span>
        </div>
        {report && (
          <button 
            onClick={() => setReport(null)}
            className="text-sm text-gray-400 hover:text-white flex items-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Cockpit
          </button>
        )}
      </nav>

      <div className="max-w-5xl mx-auto">
        {!report ? (
          <>
            {/* Hero Section  */}
            <div className="text-center mb-12 space-y-4">
              <h1 className="text-4xl md:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-gray-200">
                You have a strategy.<br/>You lack discipline.
              </h1>
              <p className="text-gray-500 text-lg max-w-xl mx-auto">
                The objective second opinion your psychology needs. No signals. Just data.
              </p>
            </div>
            
            {/* Input Form */}
            <TradeEvaluationForm onSubmit={handleAudit} isLoading={loading} />
          </>
        ) : (
          /* Decision Report */
          <DecisionReport data={report} />
        )}
      </div>
    </main>
  );
}

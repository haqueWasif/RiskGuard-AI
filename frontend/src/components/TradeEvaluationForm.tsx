"use client";

import { useState } from 'react';
import { Play, AlertCircle } from 'lucide-react';

interface AuditRequest {
  symbol: string;
  strategy_type: string;
  account_balance: number;
  risk_percentage: number;
}

interface Props {
  onSubmit: (data: AuditRequest) => void;
  isLoading: boolean;
}

export default function TradeEvaluationForm({ onSubmit, isLoading }: Props) {
  const [formData, setFormData] = useState<AuditRequest>({
    symbol: "BTC/USDT",
    strategy_type: "TREND_FOLLOWING",
    account_balance: 10000,
    risk_percentage: 1.0,
  });

  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof AuditRequest, value: string | number) => {
    // Risk Validation: Max 2.0% hard cap for MVP 
    if (field === 'risk_percentage') {
       if (Number(value) > 2.0) {
         setError("High risk limits (>2%) disabled in MVP for safety.");
         return; 
       } else {
         setError(null);
       }
    }
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 max-w-lg mx-auto shadow-2xl">
      <div className="mb-6 text-center">
        <h2 className="text-xl font-bold text-gray-100">Trade Cockpit</h2>
        <p className="text-gray-400 text-sm">Input your trade parameters for audit.</p>
      </div>

      <div className="space-y-4">
        {/* 1. Asset Pair [cite: 295] */}
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Asset Pair</label>
          <select 
            value={formData.symbol}
            onChange={(e) => handleChange('symbol', e.target.value)}
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg p-3 focus:ring-2 focus:ring-teal-500 focus:outline-none"
          >
            <option value="BTC/USDT">BTC/USDT</option>
            <option value="ETH/USDT">ETH/USDT</option>
          </select>
        </div>

        {/* 2. Strategy Profile [cite: 302] */}
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Strategy Profile</label>
          <select 
            value={formData.strategy_type}
            onChange={(e) => handleChange('strategy_type', e.target.value)}
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg p-3 focus:ring-2 focus:ring-teal-500 focus:outline-none"
          >
            <option value="TREND_FOLLOWING">Trend Following</option>
            <option value="BREAKOUT" disabled>Breakout (Coming Soon)</option>
            <option value="MEAN_REVERSION">Mean Reversion</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* 3. Account Balance [cite: 305] */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Balance ($)</label>
            <input 
              type="number" 
              value={formData.account_balance}
              onChange={(e) => handleChange('account_balance', Number(e.target.value))}
              className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg p-3 focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>

          {/* 4. Risk per Trade [cite: 307] */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Risk (%)</label>
            <input 
              type="number" 
              step="0.1"
              value={formData.risk_percentage}
              onChange={(e) => handleChange('risk_percentage', Number(e.target.value))}
              className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg p-3 focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>
        </div>

        {error && (
          <div className="flex items-center text-red-400 text-xs mt-2 bg-red-900/20 p-2 rounded">
            <AlertCircle className="w-4 h-4 mr-2" />
            {error}
          </div>
        )}

        {/* Action Button [cite: 360] */}
        <button 
          onClick={() => onSubmit(formData)}
          disabled={isLoading || !!error}
          className="w-full mt-6 bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 text-white font-bold py-4 rounded-lg flex items-center justify-center transition-all shadow-lg hover:shadow-teal-500/20"
        >
          {isLoading ? (
            <span className="animate-pulse">Analyzing Market Structure...</span>
          ) : (
            <>
              <Play className="w-5 h-5 mr-2 fill-current" />
              RUN AUDIT
            </>
          )}
        </button>
      </div>
    </div>
  );
}
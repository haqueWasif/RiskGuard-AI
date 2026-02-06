import { CheckCircle, AlertTriangle, XCircle, Shield, Activity } from 'lucide-react';
import clsx from 'clsx';

interface ReportProps {
  data: {
    asset: string;
    timestamp: string;
    ui_components: {
      traffic_light: { color: string; label: string };
      regime_card: { title: string; value: string; subtext: string };
      risk_card: { title: string; metric_1: string; metric_2: string };
      ai_analysis: { text: string; blockers: string[] };
    };
  };
}

export default function DecisionReport({ data }: ReportProps) {
  const { traffic_light, regime_card, risk_card, ai_analysis } = data.ui_components;

  // Determine styles based on Traffic Light color [cite: 318]
  const statusColors = {
    GREEN: "bg-green-500/10 border-green-500 text-green-400",
    YELLOW: "bg-yellow-500/10 border-yellow-500 text-yellow-400",
    RED: "bg-red-500/10 border-red-500 text-red-400",
    GREY: "bg-gray-500/10 border-gray-500 text-gray-400",
  };

  const StatusIcon = {
    GREEN: CheckCircle,
    YELLOW: AlertTriangle,
    RED: XCircle,
    GREY: Activity
  }[traffic_light.color as keyof typeof statusColors] || Activity;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Header [cite: 315] */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div>
          <h1 className="text-2xl font-mono text-white tracking-tight">{data.asset} AUDIT</h1>
          <p className="text-gray-500 text-sm font-mono">{new Date(data.timestamp).toLocaleString()}</p>
        </div>
        <div className={clsx("px-4 py-2 rounded-full border flex items-center gap-2", statusColors[traffic_light.color as keyof typeof statusColors])}>
          <StatusIcon className="w-5 h-5" />
          <span className="font-bold tracking-wider">{traffic_light.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Zone A: Regime Context (The "Battlefield") [cite: 316] */}
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-4 text-gray-400">
            <Activity className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">{regime_card.title}</h3>
          </div>
          <div className="text-xl font-bold text-white mb-2">{regime_card.value}</div>
          <p className="text-sm text-gray-400 leading-relaxed">{regime_card.subtext}</p>
        </div>

        {/* Zone B: Risk Guardrails [cite: 321] */}
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-bl-full" />
          <div className="flex items-center gap-2 mb-4 text-teal-400">
            <Shield className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">{risk_card.title}</h3>
          </div>
          
          <div className="space-y-4">
            <div>
               <div className="text-xs text-gray-500 uppercase mb-1">Recommended Stop Width</div>
               <div className="text-lg font-mono text-white">{risk_card.metric_1}</div>
            </div>
            <div>
               <div className="text-xs text-gray-500 uppercase mb-1">Max Position Size</div>
               <div className="text-lg font-mono text-white">{risk_card.metric_2}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Zone C: AI Executive Summary [cite: 325] */}
      <div className="bg-gray-800/50 border border-gray-700 p-6 rounded-xl">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Analysis Summary</h3>
        <p className="text-gray-300 leading-relaxed font-light">
          {ai_analysis.text}
        </p>
        
        {/* Blockers List */}
        {ai_analysis.blockers && ai_analysis.blockers.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <h4 className="text-xs text-red-400 font-bold uppercase mb-2">Alignment Blockers</h4>
            <ul className="list-disc list-inside space-y-1">
              {ai_analysis.blockers.map((blocker, i) => (
                <li key={i} className="text-sm text-red-300">{blocker}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
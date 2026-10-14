import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <aside aria-label="Clinical Decision Support Notice" className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-900 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <span>
          <strong className="font-semibold">CLINICAL DECISION SUPPORT DEMO:</strong> ReCare AI operates on synthetic hospital discharge data.
          Predictions and intervention recommendations are intended for care-coordination workflow triage and do not substitute for licensed clinical judgment.
        </span>
      </div>
      <span className="hidden md:inline-block text-[10px] font-mono bg-amber-100 text-amber-800 px-2 py-0.5 rounded border border-amber-300 flex-shrink-0">
        Non-Clinical Prototype
      </span>
    </aside>
  );
};

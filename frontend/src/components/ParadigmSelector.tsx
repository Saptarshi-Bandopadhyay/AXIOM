import React from "react";

export const AVAILABLE_PARADIGMS = [
  "Retrieval-Augmented Generation (RAG)",
  "LLM Fine-Tuning & Alignment",
  "AI Agents & Multi-Agent Systems",
  "Computer Vision & Multimodal Learning",
  "Reinforcement Learning & Robotics",
  "Classical Machine Learning & Tabular",
  "General / Novel AI Research",
];

interface ParadigmSelectorProps {
  selectedParadigm: string | null;
  onSelectParadigm: (paradigm: string | null) => void;
  disabled?: boolean;
}

export const ParadigmSelector: React.FC<ParadigmSelectorProps> = ({
  selectedParadigm,
  onSelectParadigm,
  disabled = false,
}) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">
          Research Paradigm (Optional override)
        </label>
        {selectedParadigm && (
          <button
            type="button"
            onClick={() => onSelectParadigm(null)}
            className="text-xs text-blue-600 hover:underline"
            disabled={disabled}
          >
            Reset to Auto-detect
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onSelectParadigm(null)}
          className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${
            selectedParadigm === null
              ? "bg-blue-50 border-blue-500 text-blue-700"
              : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
          }`}
        >
          ✨ Auto-detect
        </button>

        {AVAILABLE_PARADIGMS.map((paradigm) => {
          const isSelected = selectedParadigm === paradigm;
          return (
            <button
              key={paradigm}
              type="button"
              disabled={disabled}
              onClick={() => onSelectParadigm(paradigm)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${
                isSelected
                  ? "bg-blue-600 border-blue-600 text-white"
                  : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {paradigm}
            </button>
          );
        })}
      </div>
    </div>
  );
};

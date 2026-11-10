import React, { useState } from "react";
import { X, Send, Bot, User, Sparkles, AlertCircle } from "lucide-react";
import { apiClient } from "../api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface GroundedQnADrawerProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
}

const QUICK_PROMPTS = [
  "Are random seeds reported in the methodology?",
  "What compute hardware or GPUs were specified?",
  "Why was baseline tuning flagged?",
  "Summarize the key reporting gaps in this paper.",
];

export const GroundedQnADrawer: React.FC<GroundedQnADrawerProps> = ({
  sessionId,
  isOpen,
  onClose,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I am ReproCheck's Grounded Assistant. I can answer questions strictly based on the submitted paper and its methodology review findings.",
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isLoading) return;

    setErrorMessage(null);
    setInputQuery("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsLoading(true);

    try {
      const response = await apiClient.askQuestion(sessionId, query);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer },
      ]);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to receive grounded answer.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-lg bg-white h-full shadow-2xl flex flex-col border-l border-slate-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-blue-100 rounded-lg text-blue-700">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Grounded Review Assistant</h3>
              <p className="text-xs text-slate-500">Strictly cites paper text & findings</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Grounding Disclaimer */}
        <div className="p-2.5 bg-blue-50/70 border-b border-blue-100 text-2xs text-blue-800 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 shrink-0 text-blue-600" />
          <span>Restricted to submitted paper. External/general knowledge is refused.</span>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "user" ? "bg-slate-800 text-white" : "bg-blue-600 text-white"
                }`}
              >
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`p-3.5 rounded-xl text-xs leading-relaxed max-w-[85%] ${
                  msg.role === "user"
                    ? "bg-slate-900 text-white rounded-tr-none"
                    : "bg-slate-100 text-slate-900 rounded-tl-none border border-slate-200 whitespace-pre-wrap"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-3.5 rounded-xl text-xs bg-slate-100 text-slate-500 rounded-tl-none border border-slate-200 flex items-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                Retrieving grounded evidence...
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Quick Prompts Suggestions */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <p className="text-2xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            Suggested Inquiries
          </p>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_PROMPTS.map((prompt, pIdx) => (
              <button
                key={pIdx}
                type="button"
                disabled={isLoading}
                onClick={() => handleSendMessage(prompt)}
                className="text-2xs px-2.5 py-1 bg-white border border-slate-200 text-slate-700 rounded-md hover:border-blue-400 hover:text-blue-600 transition-colors text-left"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <div className="p-3 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask about hyperparameters, hardware, findings..."
              disabled={isLoading}
              className="flex-1 text-xs px-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isLoading}
              className={`p-2.5 rounded-lg text-white transition-colors ${
                !inputQuery.trim() || isLoading
                  ? "bg-blue-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

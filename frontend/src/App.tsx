import React, { useState, useEffect, useRef } from "react";
import { apiClient } from "./api/client";
import { SubmissionForm } from "./components/SubmissionForm";
import { ChecklistEditor } from "./components/ChecklistEditor";
import { ReviewReportView } from "./components/ReviewReportView";
import { GroundedQnADrawer } from "./components/GroundedQnADrawer";
import { ChecklistItem, ReviewReport, SessionStatus } from "./types";
import { ShieldCheck, AlertCircle, Cpu } from "lucide-react";

export const App: React.FC = () => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<SessionStatus | "IDLE">("IDLE");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Candidate checklist state
  const [candidateChecklist, setCandidateChecklist] = useState<ChecklistItem[]>([]);
  const [primaryParadigm, setPrimaryParadigm] = useState<string | null>(null);

  // Completed review report state
  const [report, setReport] = useState<ReviewReport | null>(null);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isQnaOpen, setIsQnaOpen] = useState(false);

  // Polling ref to prevent concurrent poll intervals
  const pollingRef = useRef<number | null>(null);

  const stopPolling = () => {
    if (pollingRef.current !== null) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  // Poll session status when working on an active session
  useEffect(() => {
    if (!currentSessionId) return;

    if (status === "COMPLETED" || status === "FAILED") {
      stopPolling();
      return;
    }

    const poll = async () => {
      try {
        if (status === "EXTRACTING" || status === "CLASSIFYING" || status === "PENDING_INPUT") {
          const session = await apiClient.getSession(currentSessionId);
          setStatus(session.status);

          if (session.status === "AWAITING_CHECKLIST_APPROVAL") {
            const checklistRes = await apiClient.getChecklist(currentSessionId);
            setCandidateChecklist(checklistRes.checklist);
            setPrimaryParadigm(session.paper?.primary_research_type || null);
            stopPolling();
          } else if (session.status === "FAILED") {
            setErrorMessage(session.error_message || "Session failed during processing.");
            stopPolling();
          }
        } else if (status === "REVIEWING") {
          const reportRes = await apiClient.getReviewReport(currentSessionId);
          if (reportRes.status === "COMPLETED") {
            setReport(reportRes);
            setStatus("COMPLETED");
            stopPolling();
          } else if (reportRes.status === "FAILED") {
            setErrorMessage("Methodology review failed to complete.");
            setStatus("FAILED");
            stopPolling();
          }
        }
      } catch (err: any) {
        // Continue polling on transient errors
        console.warn("Polling error:", err.message);
      }
    };

    // Run poll every 2 seconds
    pollingRef.current = window.setInterval(poll, 2000);
    poll(); // Run immediately

    return () => stopPolling();
  }, [currentSessionId, status]);

  const handleSubmitPdf = async (file: File, paradigm?: string) => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await apiClient.uploadPdf(file, paradigm);
      setCurrentSessionId(res.id);
      setStatus(res.status);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to upload PDF.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitText = async (data: {
    methodology_text: string;
    title?: string;
    primary_research_type?: string;
  }) => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await apiClient.pasteMethodology(data);
      setCurrentSessionId(res.id);
      setStatus(res.status);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit methodology text.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveChecklist = async (approvedItems: ChecklistItem[]) => {
    if (!currentSessionId) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await apiClient.approveChecklist(currentSessionId, approvedItems);
      setStatus("REVIEWING");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to approve checklist.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    stopPolling();
    setCurrentSessionId(null);
    setStatus("IDLE");
    setErrorMessage(null);
    setCandidateChecklist([]);
    setPrimaryParadigm(null);
    setReport(null);
    setIsQnaOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={handleReset}>
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-slate-900 tracking-tight text-base">ReproCheck</span>
              <span className="text-2xs text-slate-400 block -mt-1 font-medium">
                Research Methodology Reviewer
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5 font-medium">
              <Cpu className="w-3.5 h-3.5 text-blue-600" /> Free LLM Architecture
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between text-red-700 text-sm">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              type="button"
              onClick={handleReset}
              className="text-xs font-semibold underline hover:no-underline ml-4"
            >
              Start Over
            </button>
          </div>
        )}

        {/* View 1: Submission Form */}
        {status === "IDLE" && (
          <div className="space-y-6">
            <div className="text-center max-w-2xl mx-auto space-y-2 mb-8">
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Evaluate Computer Science Paper Reproducibility
              </h1>
              <p className="text-sm text-slate-600 leading-relaxed">
                ReproCheck generates a customized two-tier reproducibility checklist, verifies
                empirical methodology against verbatim paper text, and uncovers cross-section inconsistencies.
              </p>
            </div>

            <SubmissionForm
              onSubmitPdf={handleSubmitPdf}
              onSubmitText={handleSubmitText}
              isLoading={isSubmitting}
            />
          </div>
        )}

        {/* View 2: Initial Analysis Loading State */}
        {(status === "EXTRACTING" || status === "CLASSIFYING" || status === "PENDING_INPUT") && (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-4 shadow-sm max-w-xl mx-auto">
            <div className="w-12 h-12 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <h2 className="text-base font-bold text-slate-900">
              {status === "EXTRACTING" ? "Extracting Document Sections..." : "Analyzing Research Paradigm..."}
            </h2>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Extracting methodology text, identifying paper paradigm, and deriving candidate checklist criteria...
            </p>
          </div>
        )}

        {/* View 3: Human-in-the-Loop Checklist Editor */}
        {status === "AWAITING_CHECKLIST_APPROVAL" && (
          <ChecklistEditor
            checklist={candidateChecklist}
            primaryParadigm={primaryParadigm}
            onApprove={handleApproveChecklist}
            isSubmitting={isSubmitting}
          />
        )}

        {/* View 4: Review In Progress Loading State */}
        {status === "REVIEWING" && (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-4 shadow-sm max-w-xl mx-auto">
            <div className="w-12 h-12 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <h2 className="text-base font-bold text-slate-900">Evaluating Research Methodology...</h2>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Checking empirical criteria, extracting verbatim quotes, checking cross-section consistency,
              and synthesizing overall assessment...
            </p>
          </div>
        )}

        {/* View 5: Completed Review Report */}
        {status === "COMPLETED" && report && (
          <ReviewReportView
            report={report}
            onOpenQna={() => setIsQnaOpen(true)}
            onReset={handleReset}
          />
        )}

        {/* View 6: Failed Session Recovery */}
        {status === "FAILED" && !errorMessage && (
          <div className="bg-white rounded-xl border border-rose-200 p-8 text-center space-y-4 max-w-md mx-auto">
            <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
            <h2 className="text-base font-bold text-slate-900">Review Execution Failed</h2>
            <p className="text-xs text-slate-500">
              An error occurred while analyzing the paper. Please verify the input file or text and try again.
            </p>
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
            >
              Start New Review
            </button>
          </div>
        )}
      </main>

      {/* Grounded Q&A Drawer */}
      {currentSessionId && (
        <GroundedQnADrawer
          sessionId={currentSessionId}
          isOpen={isQnaOpen}
          onClose={() => setIsQnaOpen(false)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        ReproCheck — AI Research Methodology Reviewer • Open & Reproducible AI Research
      </footer>
    </div>
  );
};

export default App;

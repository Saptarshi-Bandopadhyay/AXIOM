import React, { useState } from "react";
import { ReviewReport, ReviewFinding } from "../types";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Quote,
  MessageSquare,
  FileSearch,
  CheckCircle2,
} from "lucide-react";

interface ReviewReportViewProps {
  report: ReviewReport;
  onOpenQna: () => void;
  onReset: () => void;
}

export const ReviewReportView: React.FC<ReviewReportViewProps> = ({
  report,
  onOpenQna,
  onReset,
}) => {
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [expandedQuotes, setExpandedQuotes] = useState<Record<string, boolean>>({});

  const toggleQuotes = (id: string) => {
    setExpandedQuotes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const assessment = report.overall_assessment;

  // Filter findings
  const filteredFindings = report.findings.filter((f) => {
    if (statusFilter === "ALL") return true;
    return f.status === statusFilter;
  });

  const metCount = report.findings.filter((f) => f.status === "MET").length;
  const incompleteCount = report.findings.filter((f) => f.status === "INCOMPLETE").length;
  const missingCount = report.findings.filter((f) => f.status === "MISSING").length;

  const getLabelColor = (label?: string) => {
    switch (label) {
      case "Well documented":
        return "bg-emerald-50 text-emerald-800 border-emerald-200";
      case "Partially documented":
        return "bg-amber-50 text-amber-800 border-amber-200";
      case "Insufficiently documented":
        return "bg-rose-50 text-rose-800 border-rose-200";
      default:
        return "bg-slate-50 text-slate-800 border-slate-200";
    }
  };

  const getStatusBadge = (status: ReviewFinding["status"]) => {
    switch (status) {
      case "MET":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <CheckCircle className="w-3 h-3" /> MET
          </span>
        );
      case "INCOMPLETE":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            <AlertTriangle className="w-3 h-3" /> INCOMPLETE
          </span>
        );
      case "MISSING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
            <XCircle className="w-3 h-3" /> MISSING
          </span>
        );
    }
  };

  const getSeverityBadge = (severity: ReviewFinding["severity"]) => {
    switch (severity) {
      case "CRITICAL":
        return (
          <span className="px-2 py-0.5 text-xs font-bold rounded bg-rose-50 text-rose-700 border border-rose-200">
            CRITICAL
          </span>
        );
      case "WARNING":
        return (
          <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-50 text-amber-700 border border-amber-200">
            WARNING
          </span>
        );
      case "NOTE":
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-50 text-blue-700 border border-blue-200">
            NOTE
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-blue-600 text-white">
              {report.primary_research_type || "General AI"}
            </span>
            {report.secondary_research_types?.map((sec) => (
              <span key={sec} className="px-2 py-0.5 text-xs font-medium rounded-md bg-slate-100 text-slate-600">
                {sec}
              </span>
            ))}
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-2">
            {report.title || "Methodology Review Report"}
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">Session ID: {report.session_id}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenQna}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-2 shadow-sm transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            Ask Grounded Q&A
          </button>
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-lg transition-colors"
          >
            Review Another Paper
          </button>
        </div>
      </div>

      {/* Overall Qualitative Assessment Card */}
      {assessment && (
        <div className={`p-6 rounded-xl border ${getLabelColor(assessment.label)} shadow-sm`}>
          <div className="flex items-center gap-2">
            <FileSearch className="w-5 h-5" />
            <h2 className="text-base font-bold">Overall Assessment: {assessment.label}</h2>
          </div>
          <p className="text-sm mt-2 leading-relaxed opacity-95">{assessment.summary}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-current/10">
            {/* Strengths */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" /> Methodological Strengths
              </h3>
              {assessment.strengths.length > 0 ? (
                <ul className="space-y-1 text-xs">
                  {assessment.strengths.map((str, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-600 font-bold">•</span>
                      <span>{str}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs italic opacity-75">No notable strengths specified.</p>
              )}
            </div>

            {/* Critical Gaps */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Key Reporting Gaps
              </h3>
              {assessment.critical_gaps.length > 0 ? (
                <ul className="space-y-1 text-xs">
                  {assessment.critical_gaps.map((gap, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-rose-600 font-bold">•</span>
                      <span>{gap}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs italic opacity-75">No critical gaps identified.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cross-Section Inconsistencies */}
      {report.inconsistencies && report.inconsistencies.length > 0 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-bold text-slate-900">Cross-Section Consistency Findings</h3>
          </div>
          <div className="space-y-3">
            {report.inconsistencies.map((item, idx) => (
              <div key={idx} className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-lg text-xs space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-amber-900">Sections Involved:</span>
                  {item.sections_involved.map((sec) => (
                    <span key={sec} className="px-1.5 py-0.5 rounded bg-amber-200/70 text-amber-900 font-medium">
                      {sec}
                    </span>
                  ))}
                </div>
                <p className="text-slate-800">{item.description}</p>
                {item.evidence_quotes.length > 0 && (
                  <div className="space-y-1 pt-1 border-t border-amber-200/60">
                    <p className="font-medium text-amber-900">Cited Contradictions:</p>
                    {item.evidence_quotes.map((q, qIdx) => (
                      <div key={qIdx} className="bg-white/80 p-2 rounded border border-amber-200/60 italic text-slate-700">
                        "{q}"
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Findings Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Status Filter Tabs */}
        <div className="flex items-center justify-between border-b border-slate-200 p-4 bg-slate-50 flex-wrap gap-2">
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setStatusFilter("ALL")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                statusFilter === "ALL"
                  ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Findings ({report.findings.length})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("MET")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                statusFilter === "MET"
                  ? "bg-emerald-50 text-emerald-800 shadow-sm border border-emerald-200"
                  : "text-slate-600 hover:text-emerald-700"
              }`}
            >
              MET ({metCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("INCOMPLETE")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                statusFilter === "INCOMPLETE"
                  ? "bg-amber-50 text-amber-800 shadow-sm border border-amber-200"
                  : "text-slate-600 hover:text-amber-700"
              }`}
            >
              INCOMPLETE ({incompleteCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("MISSING")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                statusFilter === "MISSING"
                  ? "bg-rose-50 text-rose-800 shadow-sm border border-rose-200"
                  : "text-slate-600 hover:text-rose-700"
              }`}
            >
              MISSING ({missingCount})
            </button>
          </div>

          <div className="text-xs text-slate-500">
            Showing {filteredFindings.length} of {report.findings.length} findings
          </div>
        </div>

        {/* Findings List */}
        <div className="divide-y divide-slate-100">
          {filteredFindings.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              No findings match the selected status filter.
            </div>
          ) : (
            filteredFindings.map((finding) => {
              const isExpanded = !!expandedQuotes[finding.criterion_id];
              const hasQuotes = finding.evidence_quotes && finding.evidence_quotes.length > 0;

              return (
                <div key={finding.criterion_id} className="p-5 hover:bg-slate-50/50 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {getStatusBadge(finding.status)}
                        {getSeverityBadge(finding.severity)}
                        <span className="text-xs font-mono text-slate-400">
                          {finding.criterion_id}
                        </span>
                      </div>

                      <h4 className="text-sm font-semibold text-slate-900">
                        {finding.criterion}
                      </h4>

                      <p className="text-xs text-slate-600 leading-relaxed">
                        {finding.description}
                      </p>

                      {/* Evidence Quote Toggle & Drawer */}
                      {hasQuotes && (
                        <div className="pt-2">
                          <button
                            type="button"
                            onClick={() => toggleQuotes(finding.criterion_id)}
                            className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            <Quote className="w-3 h-3" />
                            {isExpanded
                              ? "Hide Verbatim Evidence"
                              : `View Verbatim Evidence (${finding.evidence_quotes.length})`}
                            {isExpanded ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>

                          {isExpanded && (
                            <div className="mt-2 pl-3 border-l-2 border-blue-400 space-y-2 bg-slate-50/80 p-3 rounded-r-lg">
                              {finding.evidence_quotes.map((quote, qIdx) => (
                                <blockquote
                                  key={qIdx}
                                  className="text-xs text-slate-700 italic leading-relaxed"
                                >
                                  "{quote}"
                                </blockquote>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

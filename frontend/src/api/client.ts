/**
 * Typed API client for ReproCheck backend communication.
 * Communicates with FastAPI endpoints under /api/v1.
 */

import {
  AnswerResponse,
  ChecklistItem,
  ChecklistResponse,
  ReviewReport,
  SessionResponse,
} from "../types";

const API_BASE = "/api/v1";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === "string" 
          ? errorJson.detail 
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Use fallback errorDetail
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const apiClient = {
  /** Upload a PDF research paper */
  async uploadPdf(file: File, primaryResearchType?: string): Promise<SessionResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (primaryResearchType) {
      formData.append("primary_research_type", primaryResearchType);
    }
    const res = await fetch(`${API_BASE}/sessions/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<SessionResponse>(res);
  },

  /** Submit pasted methodology text */
  async pasteMethodology(data: {
    methodology_text: string;
    title?: string;
    primary_research_type?: string;
  }): Promise<SessionResponse> {
    const res = await fetch(`${API_BASE}/sessions/paste`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse<SessionResponse>(res);
  },

  /** Get review session status */
  async getSession(sessionId: string): Promise<SessionResponse> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
    return handleResponse<SessionResponse>(res);
  },

  /** Get generated checklist for inspection */
  async getChecklist(sessionId: string): Promise<ChecklistResponse> {
    const res = await fetch(`${API_BASE}/checklists/${sessionId}`);
    return handleResponse<ChecklistResponse>(res);
  },

  /** Approve and resume review with customized checklist */
  async approveChecklist(
    sessionId: string,
    checklist: ChecklistItem[]
  ): Promise<ChecklistResponse> {
    const res = await fetch(`${API_BASE}/checklists/${sessionId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ checklist }),
    });
    return handleResponse<ChecklistResponse>(res);
  },

  /** Get completed review findings report */
  async getReviewReport(sessionId: string): Promise<ReviewReport> {
    const res = await fetch(`${API_BASE}/reviews/${sessionId}/report`);
    return handleResponse<ReviewReport>(res);
  },

  /** Ask a question grounded in the paper and review findings */
  async askQuestion(sessionId: string, question: string): Promise<AnswerResponse> {
    const res = await fetch(`${API_BASE}/qna/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    return handleResponse<AnswerResponse>(res);
  },
};

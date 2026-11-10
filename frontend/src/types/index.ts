/**
 * TypeScript domain models and API types for ReproCheck.
 * Mirrors backend Pydantic models with exact field correspondence.
 */

export type SessionStatus =
  | "PENDING_INPUT"
  | "EXTRACTING"
  | "CLASSIFYING"
  | "AWAITING_CHECKLIST_APPROVAL"
  | "REVIEWING"
  | "COMPLETED"
  | "FAILED";

export type InputType = "PDF_UPLOAD" | "PASTED_TEXT";

export interface Paper {
  id: string;
  title: string | null;
  original_filename: string | null;
  primary_research_type: string | null;
  secondary_research_types: string[];
}

export interface SessionResponse {
  id: string;
  status: SessionStatus;
  input_type: InputType;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  paper: Paper | null;
}

export interface ChecklistItem {
  id: string;
  tier: 1 | 2;
  category: string;
  criterion: string;
  rationale: string;
  approved: boolean;
}

export interface ChecklistResponse {
  session_id: string;
  status: SessionStatus;
  checklist: ChecklistItem[];
  approved: boolean;
}

export interface ReviewFinding {
  criterion_id: string;
  criterion: string;
  status: "MET" | "INCOMPLETE" | "MISSING";
  severity: "NOTE" | "WARNING" | "CRITICAL";
  description: string;
  evidence_quotes: string[];
}

export interface InconsistencyItem {
  sections_involved: string[];
  description: string;
  evidence_quotes: string[];
}

export interface OverallAssessment {
  label: "Well documented" | "Partially documented" | "Insufficiently documented";
  summary: string;
  strengths: string[];
  critical_gaps: string[];
}

export interface ReviewReport {
  session_id: string;
  status: SessionStatus;
  title: string | null;
  primary_research_type: string | null;
  secondary_research_types: string[];
  checklist: ChecklistItem[];
  findings: ReviewFinding[];
  inconsistencies: InconsistencyItem[];
  overall_assessment: OverallAssessment | null;
}

export interface AnswerResponse {
  question: string;
  answer: string;
}

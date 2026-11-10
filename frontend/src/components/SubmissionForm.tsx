import React, { useState } from "react";
import { Upload, FileText, AlertCircle, FileCheck } from "lucide-react";
import { ParadigmSelector } from "./ParadigmSelector";

interface SubmissionFormProps {
  onSubmitPdf: (file: File, paradigm?: string) => Promise<void>;
  onSubmitText: (data: { methodology_text: string; title?: string; primary_research_type?: string }) => Promise<void>;
  isLoading: boolean;
}

export const SubmissionForm: React.FC<SubmissionFormProps> = ({
  onSubmitPdf,
  onSubmitText,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<"pdf" | "paste">("pdf");
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [methodologyText, setMethodologyText] = useState("");
  const [paperTitle, setPaperTitle] = useState("");
  const [selectedParadigm, setSelectedParadigm] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    setErrorMessage(null);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (!droppedFile.name.toLowerCase().endsWith(".pdf")) {
        setErrorMessage("Only PDF files are supported.");
        return;
      }
      if (droppedFile.size > 20 * 1024 * 1024) {
        setErrorMessage("File exceeds 20MB limit.");
        return;
      }
      setFile(droppedFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    const selected = e.target.files?.[0];
    if (selected) {
      if (selected.size > 20 * 1024 * 1024) {
        setErrorMessage("File exceeds 20MB limit.");
        return;
      }
      setFile(selected);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    try {
      if (activeTab === "pdf") {
        if (!file) {
          setErrorMessage("Please select a PDF file to submit.");
          return;
        }
        await onSubmitPdf(file, selectedParadigm || undefined);
      } else {
        if (methodologyText.trim().length < 20) {
          setErrorMessage("Methodology text must be at least 20 characters.");
          return;
        }
        await onSubmitText({
          methodology_text: methodologyText.trim(),
          title: paperTitle.trim() || undefined,
          primary_research_type: selectedParadigm || undefined,
        });
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Submission failed. Please check inputs.");
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Tab Switcher */}
      <div className="flex border-b border-slate-200 bg-slate-50">
        <button
          type="button"
          onClick={() => { setActiveTab("pdf"); setErrorMessage(null); }}
          className={`flex-1 py-3 px-4 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${
            activeTab === "pdf"
              ? "bg-white text-blue-600 border-b-2 border-blue-600 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <Upload className="w-4 h-4" />
          Upload Research Paper (PDF)
        </button>
        <button
          type="button"
          onClick={() => { setActiveTab("paste"); setErrorMessage(null); }}
          className={`flex-1 py-3 px-4 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${
            activeTab === "paste"
              ? "bg-white text-blue-600 border-b-2 border-blue-600 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          <FileText className="w-4 h-4" />
          Paste Methodology Text
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {errorMessage && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Tab 1: PDF Upload */}
        {activeTab === "pdf" && (
          <div className="space-y-4">
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleFileDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                isDragging
                  ? "border-blue-500 bg-blue-50/50"
                  : file
                  ? "border-emerald-400 bg-emerald-50/30"
                  : "border-slate-300 hover:border-slate-400 bg-slate-50/50"
              }`}
            >
              {file ? (
                <div className="flex flex-col items-center justify-center space-y-2">
                  <FileCheck className="w-10 h-10 text-emerald-600" />
                  <p className="font-medium text-slate-800 text-sm">{file.name}</p>
                  <p className="text-xs text-slate-500">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for review
                  </p>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="text-xs text-red-600 hover:underline pt-1"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center space-y-3">
                  <Upload className="w-10 h-10 text-slate-400" />
                  <div>
                    <label
                      htmlFor="pdf-upload"
                      className="cursor-pointer text-sm font-semibold text-blue-600 hover:underline"
                    >
                      Click to upload
                    </label>
                    <span className="text-sm text-slate-500"> or drag and drop</span>
                  </div>
                  <p className="text-xs text-slate-400">PDF papers up to 20MB</p>
                  <input
                    id="pdf-upload"
                    type="file"
                    accept=".pdf,application/pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Paste Methodology */}
        {activeTab === "paste" && (
          <div className="space-y-4">
            <div>
              <label htmlFor="paper-title" className="block text-sm font-medium text-slate-700 mb-1">
                Paper Title (Optional)
              </label>
              <input
                id="paper-title"
                type="text"
                value={paperTitle}
                onChange={(e) => setPaperTitle(e.target.value)}
                placeholder="e.g., Dense Passage Retrieval for Open Domain Question Answering"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label htmlFor="methodology-text" className="block text-sm font-medium text-slate-700">
                  Methodology & Approach Text
                </label>
                <span className="text-xs text-slate-400">
                  {methodologyText.length} characters
                </span>
              </div>
              <textarea
                id="methodology-text"
                rows={8}
                value={methodologyText}
                onChange={(e) => setMethodologyText(e.target.value)}
                placeholder="Paste the methodology, model architecture, training configuration, hyperparameters, or experimental setup here..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono"
              />
            </div>
          </div>
        )}

        {/* Paradigm Selector */}
        <ParadigmSelector
          selectedParadigm={selectedParadigm}
          onSelectParadigm={setSelectedParadigm}
          disabled={isLoading}
        />

        {/* Submit Button */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={isLoading || (activeTab === "pdf" && !file) || (activeTab === "paste" && !methodologyText.trim())}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium text-white shadow-sm flex items-center gap-2 transition-all ${
              isLoading || (activeTab === "pdf" && !file) || (activeTab === "paste" && !methodologyText.trim())
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyzing Submission...
              </>
            ) : (
              <>Start Methodology Review</>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

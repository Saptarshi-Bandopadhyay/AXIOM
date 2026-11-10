import React, { useState } from "react";
import { ChecklistItem } from "../types";
import { CheckCircle2, Plus, Trash2, Edit2, Sparkles, Check, X } from "lucide-react";

interface ChecklistEditorProps {
  checklist: ChecklistItem[];
  primaryParadigm?: string | null;
  onApprove: (approvedChecklist: ChecklistItem[]) => Promise<void>;
  isSubmitting: boolean;
}

export const ChecklistEditor: React.FC<ChecklistEditorProps> = ({
  checklist: initialItems,
  primaryParadigm,
  onApprove,
  isSubmitting,
}) => {
  const [items, setItems] = useState<ChecklistItem[]>(initialItems);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editCriterionText, setEditCriterionText] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);

  // New criterion state
  const [newTier, setNewTier] = useState<1 | 2>(2);
  const [newCategory, setNewCategory] = useState("Custom Criterion");
  const [newQuestion, setNewQuestion] = useState("");
  const [newRationale, setNewRationale] = useState("");

  const toggleApproval = (id: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, approved: !item.approved } : item
      )
    );
  };

  const removeItem = (id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  const startEdit = (item: ChecklistItem) => {
    setEditingId(item.id);
    setEditCriterionText(item.criterion);
  };

  const saveEdit = (id: string) => {
    if (!editCriterionText.trim()) return;
    setItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, criterion: editCriterionText.trim() } : item
      )
    );
    setEditingId(null);
  };

  const handleAddCriterion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;

    const newItem: ChecklistItem = {
      id: `CUSTOM-${Date.now()}`,
      tier: newTier,
      category: newCategory.trim() || "Custom",
      criterion: newQuestion.trim(),
      rationale: newRationale.trim() || "User-added custom reproducibility check.",
      approved: true,
    };

    setItems((prev) => [...prev, newItem]);
    setNewQuestion("");
    setNewRationale("");
    setShowAddForm(false);
  };

  const approvedCount = items.filter((i) => i.approved).length;

  const tier1Items = items.filter((i) => i.tier === 1);
  const tier2Items = items.filter((i) => i.tier === 2);

  const renderItemList = (list: ChecklistItem[], tierTitle: string, tierBadge: string) => (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-slate-100 text-slate-700">
          {tierBadge}
        </span>
        <h3 className="text-sm font-semibold text-slate-800">{tierTitle}</h3>
        <span className="text-xs text-slate-400">({list.length} criteria)</span>
      </div>

      <div className="space-y-2">
        {list.map((item) => (
          <div
            key={item.id}
            className={`p-4 rounded-lg border transition-all ${
              item.approved
                ? "border-slate-200 bg-white hover:border-slate-300"
                : "border-slate-200 bg-slate-50 opacity-60"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3 flex-1">
                <input
                  type="checkbox"
                  checked={item.approved}
                  onChange={() => toggleApproval(item.id)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />

                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-blue-50 text-blue-700">
                      {item.category}
                    </span>
                    <span className="text-xs font-mono text-slate-400">{item.id}</span>
                  </div>

                  {editingId === item.id ? (
                    <div className="flex items-center gap-2 mt-1">
                      <input
                        type="text"
                        value={editCriterionText}
                        onChange={(e) => setEditCriterionText(e.target.value)}
                        className="flex-1 px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => saveEdit(item.id)}
                        className="p-1 text-emerald-600 hover:bg-emerald-50 rounded"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="p-1 text-slate-400 hover:bg-slate-100 rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <p className={`text-sm ${item.approved ? "text-slate-900 font-medium" : "text-slate-500 line-through"}`}>
                      {item.criterion}
                    </p>
                  )}

                  <p className="text-xs text-slate-500 italic">
                    Why: {item.rationale}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                {editingId !== item.id && (
                  <button
                    type="button"
                    onClick={() => startEdit(item)}
                    className="p-1.5 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100"
                    title="Edit criterion"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => removeItem(item.id)}
                  className="p-1.5 text-slate-400 hover:text-red-600 rounded hover:bg-red-50"
                  title="Remove criterion"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="border-b border-slate-100 pb-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-slate-900">Review & Customize Checklist</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            ReproCheck generated {items.length} criteria based on the detected paradigm:{" "}
            <span className="font-semibold text-slate-700">{primaryParadigm || "General AI"}</span>.
            Toggle, edit, or add criteria before approving the evaluation.
          </p>
        </div>

        <button
          type="button"
          disabled={approvedCount === 0 || isSubmitting}
          onClick={() => onApprove(items)}
          className={`px-5 py-2.5 rounded-lg text-sm font-semibold text-white shadow-sm flex items-center justify-center gap-2 transition-all ${
            approvedCount === 0 || isSubmitting
              ? "bg-emerald-300 cursor-not-allowed"
              : "bg-emerald-600 hover:bg-emerald-700"
          }`}
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Starting Review...
            </>
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4" />
              Approve {approvedCount} Criteria & Run Review
            </>
          )}
        </button>
      </div>

      {/* Tier 1 Section */}
      {renderItemList(tier1Items, "Tier 1: Universal Empirical Rigor", "Tier 1")}

      {/* Tier 2 Section */}
      {renderItemList(tier2Items, "Tier 2: Paradigm & Domain Specific Checks", "Tier 2")}

      {/* Add Criterion Section */}
      {showAddForm ? (
        <form onSubmit={handleAddCriterion} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Add New Criterion</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Tier</label>
              <select
                value={newTier}
                onChange={(e) => setNewTier(Number(e.target.value) as 1 | 2)}
                className="w-full text-xs px-2 py-1.5 border rounded bg-white"
              >
                <option value={1}>Tier 1 (Universal Rigor)</option>
                <option value={2}>Tier 2 (Domain Specific)</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Category</label>
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                placeholder="e.g., Evaluation Metrics"
                className="w-full text-xs px-2 py-1.5 border rounded"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 block mb-1">Criterion Question</label>
            <input
              type="text"
              value={newQuestion}
              onChange={(e) => setNewQuestion(e.target.value)}
              placeholder="e.g., Does the paper report human evaluation inter-annotator agreement (Cohen's Kappa)?"
              className="w-full text-xs px-2 py-1.5 border rounded"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 block mb-1">Rationale</label>
            <input
              type="text"
              value={newRationale}
              onChange={(e) => setNewRationale(e.target.value)}
              placeholder="Why this check is necessary..."
              className="w-full text-xs px-2 py-1.5 border rounded"
            />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-200 rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
            >
              Add Criterion
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="w-full py-2.5 border-2 border-dashed border-slate-200 hover:border-slate-300 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Custom Criterion
        </button>
      )}
    </div>
  );
};

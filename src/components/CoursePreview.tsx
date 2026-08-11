import React from 'react';
import type { CoursePreviewData } from '../lib/api';

interface CoursePreviewProps {
  previewData: CoursePreviewData;
  onConfirm?: () => void | Promise<void>;
  onRegenerate?: () => void;
  isSaving?: boolean;
}

export const CoursePreview: React.FC<CoursePreviewProps> = ({
  previewData,
  onConfirm,
  onRegenerate,
  isSaving = false,
}) => {
  const [activeModuleIndex, setActiveModuleIndex] = React.useState(0);
  const [saving, setSaving] = React.useState(false);

  const handleConfirm = async () => {
    if (!onConfirm) return;
    setSaving(true);
    try {
      await onConfirm();
    } finally {
      setSaving(false);
    }
  };

  const busy = isSaving || saving;
  const currentModule = previewData.modules[activeModuleIndex];

  if (!currentModule) {
    return (
      <div className="flex h-full items-center justify-center bg-neutral-900 text-neutral-400">
        No modules in this course preview.
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto h-[90vh] flex bg-neutral-900 rounded-3xl border border-neutral-700 shadow-2xl overflow-hidden">
      <div className="w-80 border-r border-neutral-700 bg-neutral-950 flex flex-col">
        <div className="p-6 border-b border-neutral-700">
          <h1 className="text-xl font-bold text-white">{previewData.title}</h1>
          <p className="text-sm text-neutral-400 mt-2 line-clamp-3">
            {previewData.description}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-1 custom-scroll">
          {previewData.modules.map((module, idx) => (
            <button
              key={idx}
              onClick={() => setActiveModuleIndex(idx)}
              className={`w-full text-left px-4 py-4 rounded-xl transition-all ${
                activeModuleIndex === idx
                  ? 'bg-neutral-800 text-white'
                  : 'hover:bg-neutral-900 text-neutral-400'
              }`}
            >
              <div className="font-medium text-sm">{module.module_title}</div>
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-neutral-700 flex gap-3">
          <button
            onClick={handleConfirm}
            disabled={busy}
            className="flex-1 bg-green-600 hover:bg-green-500 py-3 rounded-2xl font-semibold text-sm transition-all disabled:opacity-70 text-white"
          >
            {busy ? 'Saving...' : 'Save Course'}
          </button>

          <button
            onClick={onRegenerate}
            disabled={busy}
            className="flex-1 bg-neutral-800 hover:bg-neutral-700 py-3 rounded-2xl font-semibold text-sm transition-all text-white"
          >
            Regenerate
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-10 custom-scroll">
        <div className="max-w-3xl">
          <h2 className="text-3xl font-semibold text-white mb-8">
            {currentModule.module_title}
          </h2>

          <div className="mb-10">
            <h3 className="text-sm uppercase tracking-widest text-neutral-500 mb-4">
              Learning Objectives
            </h3>
            <ul className="space-y-3 text-neutral-300">
              {currentModule.learning_objectives.map((obj, i) => (
                <li key={i} className="flex gap-3">
                  <span className="text-violet-400 mt-1">•</span>
                  <span>{obj}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mb-10">
            <h3 className="text-sm uppercase tracking-widest text-neutral-500 mb-4">
              Assigned Readings
            </h3>
            <div className="space-y-4">
              {currentModule.assigned_readings.map((book, i) => (
                <div
                  key={i}
                  className="bg-neutral-800 p-6 rounded-2xl border border-neutral-700"
                >
                  <p className="font-semibold text-white">{book.title}</p>
                  <p className="text-neutral-400 mt-1">{book.authors}</p>
                  {book.link && (
                    <a
                      href={book.link}
                      target="_blank"
                      rel="noreferrer"
                      className="text-violet-400 text-sm hover:underline mt-3 inline-block"
                    >
                      View on Google Books →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm uppercase tracking-widest text-neutral-500 mb-4">
              Assignments
            </h3>
            <div className="space-y-6">
              {currentModule.assignments.map((assignment, i) => (
                <div
                  key={i}
                  className="bg-neutral-800 p-6 rounded-2xl border border-neutral-700"
                >
                  <p className="font-medium text-white text-lg">
                    {assignment.assignment_title}
                  </p>
                  <p className="text-neutral-400 mt-3 leading-relaxed">
                    {assignment.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

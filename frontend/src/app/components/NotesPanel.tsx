"use client";

import { useState, useEffect, useCallback } from "react";
import { listNotes, createNote, deleteNote } from "@/lib/api";
import { Note } from "@/lib/types";

interface NotesPanelProps {
  jobId: string;
}

export default function NotesPanel({ jobId }: NotesPanelProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newNote, setNewNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadNotes = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await listNotes(jobId);
      setNotes(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load notes");
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    if (!newNote.trim()) return;

    setSubmitting(true);
    try {
      await createNote(jobId, { content: newNote.trim() });
      setNewNote("");
      loadNotes();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to add note");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteNote(noteId: string) {
    if (!confirm("Delete this note?")) return;

    try {
      await deleteNote(jobId, noteId);
      loadNotes();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to delete note");
    }
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h3 className="font-medium text-cc-dark">Notes</h3>
      </div>

      {/* Add Note Form */}
      <form onSubmit={handleAddNote} className="p-4 border-b border-gray-100">
        <textarea
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="Add a note..."
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid resize-none"
          disabled={submitting}
        />
        <div className="mt-2 flex justify-end">
          <button
            type="submit"
            disabled={!newNote.trim() || submitting}
            className="px-3 py-1.5 bg-cc-dark text-white text-sm rounded hover:bg-cc-mid transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Adding..." : "Add Note"}
          </button>
        </div>
      </form>

      {/* Notes List */}
      <div className="max-h-[400px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin h-6 w-6 border-4 border-cc-mid border-t-transparent rounded-full" />
          </div>
        ) : error ? (
          <div className="p-4 text-sm text-red-600">{error}</div>
        ) : notes.length === 0 ? (
          <div className="p-4 text-sm text-gray-500 text-center">
            No notes yet. Add one above!
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {notes.map((note) => (
              <div
                key={note.id}
                className="p-4 hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-start justify-between">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {note.content}
                  </p>
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    className="text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 ml-2 flex-shrink-0"
                    title="Delete note"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {formatDate(note.created_at)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

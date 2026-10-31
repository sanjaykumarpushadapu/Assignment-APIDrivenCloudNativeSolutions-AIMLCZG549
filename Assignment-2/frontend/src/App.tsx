import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  X,
  FileText,
  HeartPulse,
  LoaderCircle,
  Send,
  ShieldCheck,
} from "lucide-react";
import { useId, useRef, useState, type FormEvent } from "react";

import {
  analyzeSupportMessage,
  askKnowledgeQuestion,
  ApiError,
  type AnalysisResponse,
  type KnowledgeSource,
} from "./api";

interface ChatEntry {
  role: "staff" | "assistant";
  text: string;
  sources?: KnowledgeSource[];
  abstained?: boolean;
  isError?: boolean;
}

// Translate transport failures into an action the staff member can take.
function errorText(error: unknown): string {
  if (error instanceof ApiError && error.status === 0) {
    return "Unable to connect. Please try again shortly.";
  }
  if (error instanceof ApiError && error.status === 422) {
    return "Please check your message and try again.";
  }
  return "This request could not be completed. Please try again.";
}

function classificationLabel(classification: AnalysisResponse["classification"]): string {
  if (typeof classification === "string") {
    return classification;
  }

  for (const key of ["category", "label", "primary_category"]) {
    const value = classification[key];
    if (typeof value === "string") {
      return value;
    }
  }

  return "Staff review";
}

function requiresStaffReview(classification: AnalysisResponse["classification"]): boolean {
  return (
    typeof classification !== "string" &&
    (classification.needs_staff_review === true ||
      classification.review_required === true ||
      classification.status === "staff_review")
  );
}

// Keep citations compact; inspect one complete passage at a time in a native dialog.
function SourceList({ sources }: { sources: KnowledgeSource[] }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [selected, setSelected] = useState(0);
  const source = sources[selected];
  if (!source) return null;

  return (
    <div className="sources">
      <span className="eyebrow">Sources</span>
      <div className="source-links">
        {sources.map((item, index) => (
          <button className="source-chip" key={item.chunk_id} type="button"
            title={item.source_title}
            onClick={() => { setSelected(index); dialog.current?.showModal(); }}>
            <FileText aria-hidden="true" size={14} />
            <span>{item.section || item.source_title}</span>
            <ChevronRight aria-hidden="true" size={12} />
          </button>
        ))}
      </div>
      <dialog className="source-dialog" ref={dialog} aria-labelledby={titleId}>
        <div className="dialog-top">
          <span className="eyebrow">Source passage · {selected + 1} of {sources.length}</span>
          <button className="icon-button" type="button" aria-label="Close source"
            onClick={() => dialog.current?.close()}><X size={18} /></button>
        </div>
        <h2 id={titleId}>{source.section || source.source_title}</h2>
        <p className="source-reference">{source.source_title}</p>
        <p className="source-passage">{source.text}</p>
        <div className="dialog-bottom">
          <a href={source.source_url} target="_blank" rel="noreferrer">
            Open original source <ExternalLink size={14} aria-hidden="true" />
          </a>
          <div className="pager">
            <button type="button" className="icon-button" aria-label="Previous source"
              disabled={selected === 0} onClick={() => setSelected(selected - 1)}><ChevronLeft size={18} /></button>
            <button type="button" className="icon-button" aria-label="Next source"
              disabled={selected === sources.length - 1} onClick={() => setSelected(selected + 1)}><ChevronRight size={18} /></button>
          </div>
        </div>
      </dialog>
    </div>
  );
}

export default function App() {
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [question, setQuestion] = useState("");
  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  // Page through exchanges instead of growing the conversation down the page.
  const [chatPage, setChatPage] = useState(0);

  const submitAnalysis = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedMessage = message.trim();
    if (!normalizedMessage) {
      return;
    }

    setAnalysis(null);
    setAnalysisError(null);
    setIsAnalyzing(true);
    try {
      setAnalysis(await analyzeSupportMessage(normalizedMessage));
    } catch (error: unknown) {
      setAnalysisError(errorText(error));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const submitQuestion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion) {
      return;
    }

    setChatPage(Math.floor(chatEntries.length / 2));
    setChatEntries((entries) => [...entries, { role: "staff", text: normalizedQuestion }]);
    setQuestion("");
    setIsAsking(true);
    try {
      const result = await askKnowledgeQuestion(normalizedQuestion);
      setChatEntries((entries) => [
        ...entries,
        {
          role: "assistant",
          text: result.answer ?? "The service did not return an answer.",
          sources: result.sources,
          abstained: result.abstained,
        },
      ]);
    } catch (error: unknown) {
      setChatEntries((entries) => [
        ...entries,
        { role: "assistant", text: errorText(error), isError: true },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  const exchangeCount = Math.ceil(chatEntries.length / 2);
  const visibleEntries = chatEntries.slice(chatPage * 2, chatPage * 2 + 2);

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="brand-mark"><HeartPulse aria-hidden="true" size={23} /></span>
        <h1>Diabetes support</h1>
      </header>
      <main className="workspace">
        <div className="workflow-grid">
          <section className="panel support-panel" aria-labelledby="support-title">
            <div className="panel-heading">
              <h2 id="support-title">Request analysis</h2>
            </div>
            <div className="support-layout">
              <form className="analysis-form" onSubmit={submitAnalysis}>
                <div className="field-heading"><label htmlFor="support-message">Incoming message</label>{message.length >= 3600 && <span>{4000 - message.length} characters remaining</span>}</div>
                <textarea id="support-message" maxLength={4000} value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="Paste a patient support request here…" />
                <div className="form-actions">
                  <button className="primary-button" disabled={isAnalyzing || !message.trim()} type="submit">
                    {isAnalyzing ? <LoaderCircle className="spinner" size={16} aria-hidden="true" /> : <ArrowRight size={16} aria-hidden="true" />}
                    {isAnalyzing ? "Analyzing…" : "Analyze request"}
                  </button>
                </div>
              </form>
              <div className="handoff" aria-live="polite" aria-busy={isAnalyzing}>
                <h3>Summary</h3>
                {analysisError ? <p className="error-message" role="alert">{analysisError}</p> : analysis ? (
                  <div className="analysis-result">
                    <span className="category-label">{classificationLabel(analysis.classification).replace(/_/g, " ")}</span>
                    {requiresStaffReview(analysis.classification) && <span className="referral-label">Review required</span>}
                    <p>{analysis.summary}</p>
                  </div>
                ) : <p className="result-empty">Your summary will appear here.</p>}
              </div>
            </div>
          </section>

          <section className="panel knowledge-panel" aria-labelledby="knowledge-title">
            <div className="panel-heading">
              <h2 id="knowledge-title">Knowledge assistant</h2>
            </div>
            <div className="conversation" aria-live="polite" aria-busy={isAsking}>
              {exchangeCount > 1 && <div className="conversation-navigation">
                <span>Question {chatPage + 1} of {exchangeCount}</span>
                <div className="pager">
                  <button type="button" className="icon-button" aria-label="Previous question" disabled={isAsking || chatPage === 0} onClick={() => setChatPage(chatPage - 1)}><ChevronLeft size={16} /></button>
                  <button type="button" className="icon-button" aria-label="Next question" disabled={isAsking || chatPage === exchangeCount - 1} onClick={() => setChatPage(chatPage + 1)}><ChevronRight size={16} /></button>
                </div>
              </div>}
              {chatEntries.length === 0 ? (
                <p className="chat-empty">Your answer will appear here.</p>
              ) : <div className="exchange" key={chatPage}>
                {visibleEntries.map((entry, index) => <div className={`chat-entry chat-entry--${entry.role}${entry.isError ? " chat-entry--error" : ""}`} key={`${entry.role}-${index}`} role={entry.isError ? "alert" : undefined}>
                  <span className="entry-label">{entry.role === "staff" ? "Your question" : entry.abstained ? "Staff referral" : "Document answer"}</span>
                  <p>{entry.text}</p>
                  {entry.sources && <SourceList sources={entry.sources} />}
                </div>)}
                {isAsking && <p className="searching" role="status"><LoaderCircle size={16} className="spinner" aria-hidden="true" />Searching documents…</p>}
              </div>}
            </div>
            <form className="question-form" onSubmit={submitQuestion}>
              <label htmlFor="question">Ask a question</label>
              <div className="question-input">
                <textarea id="question" maxLength={2000} rows={2} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about diabetes information…" />
                <button type="submit" className="send-button" aria-label="Send question" title="Send question" disabled={isAsking || !question.trim()}>
                  {isAsking ? <LoaderCircle size={18} className="spinner" aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
                </button>
              </div>
            </form>
          </section>
        </div>
      </main>
      <footer className="app-footer"><ShieldCheck size={14} aria-hidden="true" /><span>Review responses before sharing with a patient.</span></footer>
    </div>
  );
}

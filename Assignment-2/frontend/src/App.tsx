import {
  Activity,
  ArrowRight,
  BookOpen,
  CircleAlert,
  FileText,
  HeartPulse,
  LoaderCircle,
  MessageSquareText,
  Send,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import {
  analyzeSupportMessage,
  askKnowledgeQuestion,
  getServiceMetadata,
  type AnalysisResponse,
  type KnowledgeSource,
  type ServiceMetadata,
} from "./api";

type ApiConnection = "checking" | "online" | "offline";
type ReadinessState = "checking" | "connected" | "ready" | "offline" | "not-configured";

interface ChatEntry {
  role: "staff" | "assistant";
  text: string;
  sources?: KnowledgeSource[];
  isError?: boolean;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "An unexpected error occurred.";
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

const readinessStyles: Record<
  ReadinessState,
  { label: string; color: string; dot: string }
> = {
  checking: { label: "Checking", color: "text-[#687a70]", dot: "bg-[#9aab9f]" },
  connected: { label: "Connected", color: "text-[#28684f]", dot: "bg-[#348260]" },
  ready: { label: "Ready", color: "text-[#28684f]", dot: "bg-[#348260]" },
  offline: { label: "Offline", color: "text-[#a14d3d]", dot: "bg-[#bd7040]" },
  "not-configured": {
    label: "Not configured",
    color: "text-[#9b6828]",
    dot: "bg-[#c18a43]",
  },
};

function componentReadiness(ready: boolean | undefined): ReadinessState {
  if (ready === undefined) {
    return "checking";
  }

  return ready ? "ready" : "not-configured";
}

function ReadinessCell({ label, state }: { label: string; state: ReadinessState }) {
  const style = readinessStyles[state];

  return (
    <div className="flex min-w-0 items-center justify-between gap-3 py-2 sm:justify-start sm:gap-2">
      <p className="truncate text-xs font-medium text-[#718078]">{label}</p>
      <span className={`inline-flex shrink-0 items-center gap-1.5 text-xs font-semibold ${style.color}`}>
        <span aria-hidden="true" className={`size-1.5 rounded-full ${style.dot}`} />
        {style.label}
      </span>
    </div>
  );
}

function SourceList({ sources }: { sources: KnowledgeSource[] }) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-[#e6ebe7] pt-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#718078]">
        Sources
      </p>
      <ul className="space-y-2">
        {sources.map((source, index) => {
          const title = source.title ?? source.source_id ?? source.id ?? `Source ${index + 1}`;
          const excerpt = source.excerpt ?? source.text;

          return (
            <li
              className="flex gap-2 text-sm text-[#52645b]"
              key={source.source_id ?? source.id ?? `${title}-${index}`}
            >
              <FileText aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-[#497461]" />
              <div className="min-w-0">
                <p className="font-medium text-[#263a31]">{title}</p>
                {source.section && <p className="text-xs">{source.section}</p>}
                {excerpt && <p className="mt-1 line-clamp-3 text-xs">{excerpt}</p>}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default function App() {
  const [apiConnection, setApiConnection] = useState<ApiConnection>("checking");
  const [metadata, setMetadata] = useState<ServiceMetadata | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [question, setQuestion] = useState("");
  const [chatEntries, setChatEntries] = useState<ChatEntry[]>([]);
  const [isAsking, setIsAsking] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    getServiceMetadata(controller.signal)
      .then((result) => {
        setMetadata(result);
        setApiConnection("online");
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setApiError(errorText(error));
          setApiConnection("offline");
        }
      });

    return () => controller.abort();
  }, []);

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
          sources: result.sources ?? [],
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

  const readyCount = metadata
    ? [metadata.classifier, metadata.summarizer, metadata.knowledge_index].filter(
        (component) => component.ready,
      ).length
    : 0;

  return (
    <div className="min-h-screen bg-transparent text-[#1d2924]">
      <header className="border-b border-[#e0e6e1] bg-[#fbfcfa]">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-4 py-3 sm:px-7">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-lg bg-[#174737] text-white">
              <HeartPulse aria-hidden="true" className="size-5" />
            </span>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#527264]">
                Care operations
              </p>
              <p className="text-sm font-semibold text-[#21372e]">Diabetes support</p>
            </div>
          </div>
          <div
            aria-live="polite"
            className="flex items-center gap-2 text-xs font-semibold text-[#52645b]"
          >
            <span
              className={`size-2 rounded-full ${
                apiConnection === "online"
                  ? "bg-[#348260]"
                  : apiConnection === "offline"
                    ? "bg-[#bd7040]"
                    : "animate-pulse bg-[#9aab9f]"
              }`}
            />
            {apiConnection === "online"
              ? "API connected"
              : apiConnection === "offline"
                ? "API unavailable"
                : "Connecting"}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-4 py-6 sm:px-7 sm:py-8">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.13em] text-[#658071]">
              Clinic staff workspace
            </p>
            <h1 className="mt-2 text-2xl font-semibold leading-tight tracking-tight text-[#1b3027] sm:text-3xl">
              Diabetes support desk
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#65756d]">
              Staff review is required before any information is shared with a patient.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-[#63746b]">
            <Activity aria-hidden="true" className="size-4 text-[#47735e]" />
            {metadata
              ? `${readyCount} of 3 AI components ${readyCount === 1 ? "is" : "are"} ready`
              : "Checking AI services"}
          </div>
        </div>

        {apiConnection === "offline" && (
          <div
            className="mt-4 flex items-start gap-3 rounded-lg border border-[#ead8c7] bg-[#fff9f2] px-3.5 py-2.5 text-sm text-[#805a36]"
            role="alert"
          >
            <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            <span>{apiError ?? "The API is unavailable."}</span>
          </div>
        )}
        {apiConnection === "online" && readyCount < 3 && (
          <div
            className="mt-4 flex items-center gap-2.5 rounded-lg border border-[#ead8c7] bg-[#fff9f2] px-3.5 py-2.5 text-sm text-[#805a36]"
            role="status"
          >
            <CircleAlert aria-hidden="true" className="size-4 shrink-0" />
            <span>
              <strong className="font-semibold">AI services are not fully configured.</strong>{" "}
              Analysis and Q&amp;A require configured models and a knowledge index.
            </span>
          </div>
        )}

        <div className="mt-4 grid grid-cols-1 gap-x-6 border-y border-[#e1e7e2] py-1 sm:grid-cols-2 xl:grid-cols-4">
          <ReadinessCell
            label="API"
            state={
              apiConnection === "online"
                ? "connected"
                : apiConnection === "offline"
                  ? "offline"
                  : "checking"
            }
          />
          <ReadinessCell
            label="Request classifier"
            state={componentReadiness(metadata?.classifier.ready)}
          />
          <ReadinessCell
            label="Summarizer"
            state={componentReadiness(metadata?.summarizer.ready)}
          />
          <ReadinessCell
            label="Knowledge index"
            state={componentReadiness(metadata?.knowledge_index.ready)}
          />
        </div>

        <div className="mt-5 grid gap-5 xl:grid-cols-2">
          <section className="overflow-hidden rounded-lg border border-[#dfe6e0] bg-white shadow-[0_8px_24px_rgba(27,48,39,0.04)]">
            <div className="flex items-start gap-3 border-b border-[#e7ece8] px-5 py-4 sm:px-6">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-[#e8f0ea] text-[#32634c]">
                <MessageSquareText aria-hidden="true" className="size-[18px]" />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#718078]">
                  Request analysis
                </p>
                <h2 className="mt-1 text-lg font-semibold text-[#24382f]">Support message</h2>
              </div>
            </div>

            <div className="p-5 sm:p-6">
              <form className="space-y-3" onSubmit={submitAnalysis}>
                <label
                  className="block text-sm font-semibold text-[#34483e]"
                  htmlFor="support-message"
                >
                  Incoming support message
                </label>
                <textarea
                  className="min-h-36 w-full rounded-lg border border-[#d5dfd7] bg-[#fcfdfb] px-3.5 py-3 text-sm leading-6 text-[#25382f] outline-none transition placeholder:text-[#94a198] focus:border-[#4a7b61] focus:ring-2 focus:ring-[#dcebe1]"
                  id="support-message"
                  maxLength={4000}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="I need to move my diabetes education appointment, and I cannot find the preparation leaflet."
                  value={message}
                />
                <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                  <p className="text-xs text-[#7b8981]">{message.length} / 4000</p>
                  <button
                    className="inline-flex items-center gap-2 rounded-lg bg-[#174737] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#225a46] focus:outline-none focus:ring-2 focus:ring-[#86aa93] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={isAnalyzing || !message.trim()}
                    type="submit"
                  >
                    {isAnalyzing ? (
                      <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
                    ) : (
                      <ArrowRight aria-hidden="true" className="size-4" />
                    )}
                    Analyze request
                  </button>
                </div>
              </form>

              <div className="mt-6 border-t border-[#e7ece8] pt-5" aria-live="polite">
                <div className="flex items-center gap-2">
                  <ShieldCheck aria-hidden="true" className="size-4 text-[#497461]" />
                  <h3 className="text-sm font-semibold text-[#34483e]">Handoff summary</h3>
                </div>
                {analysisError && (
                  <div
                    className="mt-3 flex items-start gap-2 rounded-lg border border-[#ead8c7] bg-[#fff9f2] px-3.5 py-3 text-sm text-[#805a36]"
                    role="alert"
                  >
                    <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
                    {analysisError}
                  </div>
                )}
                {analysis ? (
                  <div className="mt-4 space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-xs font-medium text-[#718078]">Primary category</p>
                        <p className="mt-1 text-base font-semibold text-[#24382f]">
                          {classificationLabel(analysis.classification)}
                        </p>
                      </div>
                      {requiresStaffReview(analysis.classification) && (
                        <span className="rounded-full bg-[#fff1dc] px-3 py-1 text-xs font-semibold text-[#8b5a21]">
                          Staff review
                        </span>
                      )}
                    </div>
                    <p className="text-sm leading-6 text-[#52645b]">{analysis.summary}</p>
                  </div>
                ) : (
                  !analysisError && (
                    <p className="mt-3 text-sm leading-6 text-[#78867e]">
                      The handoff result will appear here after analysis.
                    </p>
                  )
                )}
              </div>
            </div>
          </section>

          <section className="flex min-h-[520px] flex-col overflow-hidden rounded-lg border border-[#dfe6e0] bg-white shadow-[0_8px_24px_rgba(27,48,39,0.04)]">
            <div className="flex items-start gap-3 border-b border-[#e7ece8] px-5 py-4 sm:px-6">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-[#f8eee0] text-[#8c6330]">
                <BookOpen aria-hidden="true" className="size-[18px]" />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#718078]">
                  Document Q&amp;A
                </p>
                <h2 className="mt-1 text-lg font-semibold text-[#24382f]">
                  Knowledge assistant
                </h2>
              </div>
            </div>

            <div className="flex min-h-0 flex-1 flex-col">
              <div
                aria-live="polite"
                className="flex-1 space-y-4 overflow-y-auto px-5 py-5 sm:px-6"
                role="log"
              >
                {chatEntries.length === 0 ? (
                  <div className="flex h-full min-h-40 flex-col items-center justify-center text-center">
                    <BookOpen aria-hidden="true" className="size-6 text-[#8ba092]" />
                    <p className="mt-3 text-sm font-medium text-[#53665c]">No questions yet.</p>
                  </div>
                ) : (
                  chatEntries.map((entry, index) => (
                    <div
                      aria-live={entry.isError ? "assertive" : undefined}
                      className={`max-w-[90%] rounded-lg px-4 py-3 text-sm leading-6 ${
                        entry.isError
                          ? "mr-auto border border-[#ead8c7] bg-[#fff9f2] text-[#805a36]"
                          : entry.role === "staff"
                            ? "ml-auto bg-[#eaf1eb] text-[#294337]"
                            : "mr-auto bg-[#f5f7f4] text-[#42564b]"
                      }`}
                      key={`${entry.role}-${index}`}
                      role={entry.isError ? "alert" : undefined}
                    >
                      <p className="whitespace-pre-wrap">{entry.text}</p>
                      {entry.sources && <SourceList sources={entry.sources} />}
                    </div>
                  ))
                )}
                {isAsking && (
                  <div className="flex items-center gap-2 text-sm text-[#6b7b72]" role="status">
                    <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
                    Searching approved documents
                  </div>
                )}
              </div>

              <form
                className="border-t border-[#e7ece8] bg-[#fbfcfa] p-4 sm:p-5"
                onSubmit={submitQuestion}
              >
                <label className="mb-2 block text-sm font-semibold text-[#34483e]" htmlFor="question">
                  Question
                </label>
                <div className="flex items-end gap-2">
                  <textarea
                    className="min-h-11 max-h-32 flex-1 rounded-lg border border-[#d5dfd7] bg-white px-3.5 py-2.5 text-sm leading-5 text-[#25382f] outline-none transition placeholder:text-[#94a198] focus:border-[#4a7b61] focus:ring-2 focus:ring-[#dcebe1]"
                    id="question"
                    maxLength={2000}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask about an approved clinic document."
                    value={question}
                  />
                  <button
                    aria-label="Send question"
                    className="grid size-11 shrink-0 place-items-center rounded-lg bg-[#174737] text-white transition hover:bg-[#225a46] focus:outline-none focus:ring-2 focus:ring-[#86aa93] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={isAsking || !question.trim()}
                    title="Send question"
                    type="submit"
                  >
                    <Send aria-hidden="true" className="size-4" />
                  </button>
                </div>
              </form>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { errorMessage, getTask, verifyWork } from "../api";
import type { Task } from "../types";

export default function Verification() {
  const { taskId = "" } = useParams();
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setTask(await getTask(taskId));
  }

  useEffect(() => {
    load().catch((err) => setError(errorMessage(err)));
  }, [taskId]);

  async function runVerify() {
    setBusy(true);
    setError("");
    try {
      await verifyWork(taskId);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const verification = task?.verification;

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/tasks/${taskId}`} className="text-sm text-slate-500">
          ← Back to task
        </Link>
        <h1 className="mt-2 font-display text-3xl">AI verification</h1>
        <p className="mt-1 max-w-2xl text-slate-600">
          This is an advisory check against the approved agreement. Visual quality still needs
          human review. The client makes the final decision.
        </p>
      </div>

      {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-rose-700">{error}</p>}

      {task?.status === "submitted" && (
        <button className="btn-primary" disabled={busy} onClick={runVerify}>
          {busy ? "Running verification…" : "Run AI verification"}
        </button>
      )}

      {!verification ? (
        <p className="text-slate-500">No verification result yet.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <ResultCard title="Completed" items={verification.completed_requirements} tone="emerald" />
          <ResultCard title="Missing" items={verification.missing_requirements} tone="rose" />
          <ResultCard title="Unclear" items={verification.unclear_requirements} tone="amber" />
          <div className="card p-5 md:col-span-3">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              AI recommendation
            </p>
            <p className="mt-2 font-display text-2xl capitalize">
              {verification.recommendation.replaceAll("_", " ")}
            </p>
            <p className="mt-3 text-slate-600">{verification.feedback}</p>
            <p className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
              Manual review explanation: the model only reads extracted PDF text. Images and
              layout still need a person. Do not treat this recommendation as payment approval.
            </p>
            <Link className="btn-primary mt-4" to={`/tasks/${taskId}/review`}>
              Continue to client review
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function ResultCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "emerald" | "rose" | "amber";
}) {
  const colors = {
    emerald: "border-emerald-200",
    rose: "border-rose-200",
    amber: "border-amber-200",
  };
  return (
    <div className={`card border ${colors[tone]} p-5`}>
      <h2 className="font-semibold">{title} requirements</h2>
      {items?.length ? (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-400">None</p>
      )}
    </div>
  );
}

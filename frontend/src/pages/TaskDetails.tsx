import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveAgreement,
  errorMessage,
  generateAgreement,
  getTask,
  verifyWork,
} from "../api";
import StatusBadge from "../components/StatusBadge";
import type { Task } from "../types";

export default function TaskDetails() {
  const { taskId = "" } = useParams();
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [feedback, setFeedback] = useState("");

  async function refresh() {
    const data = await getTask(taskId);
    setTask(data);
  }

  useEffect(() => {
    refresh().catch((err) => setError(errorMessage(err)));
  }, [taskId]);

  async function run(label: string, action: () => Promise<unknown>) {
    setError("");
    setBusy(label);
    try {
      await action();
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  if (!task) {
    return <p className="text-slate-600">{error || "Loading task…"}</p>;
  }

  const agreement = task.agreement;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">Task</p>
          <h1 className="font-display text-3xl">{task.title}</h1>
          <p className="mt-2 max-w-3xl text-slate-600">{task.description}</p>
        </div>
        <StatusBadge status={task.status} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card p-4">
          <p className="text-sm text-slate-500">INR budget</p>
          <p className="mt-1 text-xl font-semibold">
            {task.currency} {task.budget}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-slate-500">Deadline</p>
          <p className="mt-1 text-xl font-semibold">{task.deadline_days} days</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-slate-500">Payment</p>
          <p className="mt-1 text-xl font-semibold">
            {task.payment?.status || "not started"}
          </p>
        </div>
      </div>

      {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-rose-700">{error}</p>}

      <section className="card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-2xl">AI-generated agreement</h2>
          {(task.status === "draft" || task.status === "revision_requested") && (
            <button
              className="btn-primary"
              disabled={Boolean(busy)}
              onClick={() => run("agreement", () => generateAgreement(task.task_id))}
            >
              {busy === "agreement" ? "Generating…" : "Generate agreement"}
            </button>
          )}
        </div>
        {!agreement ? (
          <p className="mt-3 text-sm text-slate-500">No agreement yet. Generate a draft from this task.</p>
        ) : (
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <List title="Deliverables" items={agreement.deliverables} />
            <List title="Acceptance criteria" items={agreement.acceptance_criteria} />
            <List title="Client must provide" items={agreement.client_must_provide} />
            <List title="Assumptions or questions" items={agreement.assumptions_or_questions} />
          </div>
        )}

        {task.status === "agreement_pending" && (
          <AgreementDecision
            feedback={feedback}
            setFeedback={setFeedback}
            busy={busy}
            onApprove={() =>
              run("approve", () => approveAgreement(task.task_id, { approved: true }))
            }
            onRevise={() =>
              run("revise", () =>
                approveAgreement(task.task_id, {
                  approved: false,
                  feedback,
                }),
              )
            }
          />
        )}
      </section>

      <section className="card p-6">
        <h2 className="font-display text-2xl">Work and review</h2>
        <p className="mt-1 text-sm text-slate-600">
          AI verification is advisory. The client still accepts or requests a revision.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link className="btn-secondary" to={`/tasks/${task.task_id}/submit`}>
            Freelancer submission
          </Link>
          <button
            className="btn-secondary"
            disabled={task.status !== "submitted" || Boolean(busy)}
            onClick={() => run("verify", () => verifyWork(task.task_id))}
          >
            {busy === "verify" ? "Verifying…" : "Run AI verification"}
          </button>
          <Link className="btn-secondary" to={`/tasks/${task.task_id}/review`}>
            Client review
          </Link>
          <Link className="btn-primary" to={`/tasks/${task.task_id}/pay`}>
            Payment
          </Link>
        </div>

        {task.submission && (
          <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm">
            <p className="font-semibold">Latest submission</p>
            <p className="mt-1 text-slate-600">{task.submission.submission_text || "Files uploaded, text not submitted yet."}</p>
          </div>
        )}

        {task.verification && (
          <div className="mt-4">
            <Link className="text-sm font-semibold text-navy-700" to={`/tasks/${task.task_id}/verify`}>
              Open AI verification details
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      {items?.length ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-slate-400">None listed</p>
      )}
    </div>
  );
}

function AgreementDecision({
  feedback,
  setFeedback,
  busy,
  onApprove,
  onRevise,
}: {
  feedback: string;
  setFeedback: (value: string) => void;
  busy: string;
  onApprove: () => void;
  onRevise: () => void;
}) {
  return (
    <form
      className="mt-6 space-y-3 border-t border-slate-100 pt-4"
      onSubmit={(event) => {
        event.preventDefault();
        onRevise();
      }}
    >
      <p className="text-sm font-medium">Client confirmation</p>
      <textarea
        className="input min-h-24"
        placeholder="Feedback if you need changes"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
      />
      <div className="flex flex-wrap gap-3">
        <button type="button" className="btn-primary" disabled={Boolean(busy)} onClick={onApprove}>
          Confirm agreement
        </button>
        <button type="submit" className="btn-secondary" disabled={Boolean(busy)}>
          Request changes
        </button>
      </div>
    </form>
  );
}

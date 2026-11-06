import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { errorMessage, getTask, reviewWork } from "../api";
import type { Task } from "../types";

export default function ClientReview() {
  const { taskId = "" } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getTask(taskId)
      .then(setTask)
      .catch((err) => setError(errorMessage(err)));
  }, [taskId]);

  async function decide(decision: "accept" | "request_revision") {
    setBusy(true);
    setError("");
    try {
      await reviewWork(taskId, { decision, feedback: feedback || undefined });
      navigate(decision === "accept" ? `/tasks/${taskId}/pay` : `/tasks/${taskId}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <Link to={`/tasks/${taskId}`} className="text-sm text-slate-500">
          ← Back to task
        </Link>
        <h1 className="mt-2 font-display text-3xl">Client review</h1>
        <p className="mt-1 text-slate-600">
          Accept the work or request a revision. AI advice does not complete payment.
        </p>
      </div>

      {task?.verification && (
        <div className="card p-5 text-sm text-slate-600">
          Latest AI recommendation:{" "}
          <strong className="capitalize">
            {task.verification.recommendation.replaceAll("_", " ")}
          </strong>
        </div>
      )}

      <form
        className="card space-y-4 p-6"
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          void decide("request_revision");
        }}
      >
        <div>
          <label className="label" htmlFor="feedback">
            Feedback
          </label>
          <textarea
            id="feedback"
            className="input min-h-28"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Required when requesting a revision"
          />
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="btn-primary"
            disabled={busy}
            onClick={() => void decide("accept")}
          >
            Accept work
          </button>
          <button type="submit" className="btn-secondary" disabled={busy}>
            Request revision
          </button>
        </div>
      </form>
    </div>
  );
}

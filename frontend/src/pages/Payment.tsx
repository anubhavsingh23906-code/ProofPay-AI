import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { createPayment, errorMessage, getPayment, getTask } from "../api";
import type { Task } from "../types";

export default function Payment() {
  const { taskId = "" } = useParams();
  const [task, setTask] = useState<Task | null>(null);
  const [payment, setPayment] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const [taskData, paymentData] = await Promise.all([getTask(taskId), getPayment(taskId)]);
    setTask(taskData);
    setPayment(paymentData);
  }

  useEffect(() => {
    load().catch((err) => setError(errorMessage(err)));
  }, [taskId]);

  async function startCheckout() {
    setBusy(true);
    setError("");
    try {
      const result = await createPayment(taskId);
      window.location.href = result.approval_url;
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  const stored = task?.payment;

  if (!task && !error) {
    return <p className="text-slate-600">Loading payment details…</p>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <Link to={`/tasks/${taskId}`} className="text-sm text-slate-500">
          ← Back to task
        </Link>
        <h1 className="mt-2 font-display text-3xl">PayPal Sandbox checkout</h1>
      </div>

      <div className="card space-y-3 p-6">
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
          This checkout charges <strong>USD 1.00</strong> in PayPal Sandbox as a technical test
          transaction. It does not convert or replace the original INR budget, and ordinary PayPal
          Checkout is not escrow.
        </p>
        <dl className="grid gap-2 text-sm">
          <Row label="INR task budget" value={`${task?.currency || "INR"} ${task?.budget ?? "—"}`} />
          <Row label="Sandbox test amount" value="USD 1.00" />
          <Row label="Payment status" value={String(stored?.status || "not created")} />
          <Row label="Order reference" value={String(stored?.order_id || "—")} />
          <Row label="Capture ID" value={String(stored?.capture_id || "—")} />
          <Row label="Live PayPal status" value={String(payment?.paypal_live_status || "—")} />
        </dl>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        {stored?.status === "completed" ? (
          <p className="font-semibold text-emerald-700">Sandbox payment already captured.</p>
        ) : (
          <button className="btn-primary" disabled={busy || task?.status !== "client_accepted"} onClick={startCheckout}>
            {busy ? "Opening PayPal…" : "Pay USD 1.00 in Sandbox"}
          </button>
        )}
        {task?.status !== "client_accepted" && stored?.status !== "completed" && (
          <p className="text-sm text-slate-500">
            Checkout is available after the client accepts the work.
          </p>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 py-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}

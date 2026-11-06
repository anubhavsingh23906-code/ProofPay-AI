import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { capturePayment, errorMessage } from "../api";

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const taskId = params.get("task_id") || "";
  const orderId = params.get("token") || undefined;
  const [message, setMessage] = useState("Verifying the PayPal order with the server…");
  const [ok, setOk] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!taskId) {
      setError("Missing task ID. Payment was not marked complete from this redirect.");
      return;
    }
    capturePayment(taskId, orderId)
      .then((result) => {
        setOk(result.task_status === "paid" || result.payment?.status === "completed");
        setMessage(result.message || "PayPal capture finished.");
      })
      .catch((err) => setError(errorMessage(err)));
  }, [taskId, orderId]);

  return (
    <div className="mx-auto max-w-lg card p-8 text-center">
      <h1 className="font-display text-3xl">{ok ? "Payment captured" : "Payment return"}</h1>
      <p className="mt-3 text-slate-600">{error || message}</p>
      <p className="mt-4 text-sm text-slate-500">
        Returning from PayPal is not enough on its own. ProofPay asks PayPal whether the buyer
        approved the order and only then captures the USD 1.00 Sandbox test amount.
      </p>
      {taskId && (
        <Link className="btn-primary mt-6" to={`/tasks/${taskId}/pay`}>
          View payment status
        </Link>
      )}
    </div>
  );
}

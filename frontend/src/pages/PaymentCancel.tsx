import { Link, useSearchParams } from "react-router-dom";

export default function PaymentCancel() {
  const [params] = useSearchParams();
  const taskId = params.get("task_id");

  return (
    <div className="mx-auto max-w-lg card p-8 text-center">
      <h1 className="font-display text-3xl">Checkout cancelled</h1>
      <p className="mt-3 text-slate-600">
        The PayPal Sandbox order was not captured. The INR task budget is unchanged.
      </p>
      {taskId ? (
        <Link className="btn-primary mt-6" to={`/tasks/${taskId}/pay`}>
          Return to payment
        </Link>
      ) : (
        <Link className="btn-primary mt-6" to="/dashboard">
          Back to dashboard
        </Link>
      )}
    </div>
  );
}

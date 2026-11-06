import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { errorMessage, getDashboard, listTasks } from "../api";
import StatusBadge from "../components/StatusBadge";
import type { DashboardStats, TaskSummary } from "../types";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDashboard(), listTasks()])
      .then(([dashboard, items]) => {
        setStats(dashboard);
        setTasks(items);
      })
      .catch((err) => setError(errorMessage(err)));
  }, []);

  const cards = stats
    ? [
        { label: "Total tasks", value: stats.total_tasks },
        { label: "Pending agreements", value: stats.pending_agreements },
        { label: "Submitted work", value: stats.submitted_work },
        { label: "Completed tasks", value: stats.completed_tasks },
        {
          label: "Payments completed",
          value: stats.payment_status.completed,
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl">Dashboard</h1>
          <p className="mt-1 text-slate-600">Track agreements, submissions, and sandbox payments.</p>
        </div>
        <Link to="/tasks/new" className="btn-primary">
          Create task
        </Link>
      </div>

      {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-rose-700">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {cards.map((card) => (
          <div key={card.label} className="card p-5">
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className="mt-2 font-display text-3xl">{card.value}</p>
          </div>
        ))}
      </div>

      <section className="card overflow-hidden">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="font-semibold">Tasks</h2>
        </div>
        {tasks.length === 0 ? (
          <p className="px-5 py-8 text-sm text-slate-500">No tasks yet. Create one to start the workflow.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {tasks.map((task) => (
              <li key={task.task_id}>
                <Link
                  to={`/tasks/${task.task_id}`}
                  className="flex flex-col gap-2 px-5 py-4 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-semibold">{task.title}</p>
                    <p className="text-sm text-slate-500">
                      {task.currency} {task.budget} · {task.deadline_days} days
                      {task.payment?.status ? ` · PayPal ${task.payment.status}` : ""}
                    </p>
                  </div>
                  <StatusBadge status={task.status} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTask, errorMessage } from "../api";

export default function CreateTask() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [budget, setBudget] = useState("5000");
  const [deadline, setDeadline] = useState("7");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const task = await createTask({
        title,
        description,
        budget: Number(budget),
        currency: "INR",
        deadline_days: Number(deadline),
      });
      navigate(`/tasks/${task.task_id}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-3xl">Create task</h1>
      <p className="mt-2 text-slate-600">
        The budget is stored in INR. PayPal later uses a separate USD 1.00 Sandbox test amount.
      </p>

      <form onSubmit={onSubmit} className="card mt-6 space-y-4 p-6">
        <div>
          <label className="label" htmlFor="title">
            Title
          </label>
          <input
            id="title"
            className="input"
            minLength={5}
            maxLength={100}
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            className="input min-h-32"
            minLength={20}
            maxLength={2000}
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="budget">
              INR budget
            </label>
            <input
              id="budget"
              className="input"
              type="number"
              min={1}
              max={100000}
              required
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="deadline">
              Deadline (days)
            </label>
            <input
              id="deadline"
              className="input"
              type="number"
              min={1}
              max={30}
              required
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
            />
          </div>
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary" disabled={loading}>
          {loading ? "Creating…" : "Create task"}
        </button>
      </form>
    </div>
  );
}

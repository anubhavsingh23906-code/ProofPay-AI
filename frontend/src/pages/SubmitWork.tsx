import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { errorMessage, getTask, submitWork, uploadFiles } from "../api";
import type { Task } from "../types";

export default function SubmitWork() {
  const { taskId = "" } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getTask(taskId)
      .then(setTask)
      .catch((err) => setError(errorMessage(err)));
  }, [taskId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (files.length) {
        await uploadFiles(taskId, files);
      }
      await submitWork(taskId, {
        submission_text: description,
        file_names: files.map((file) => file.name),
      });
      navigate(`/tasks/${taskId}/verify`);
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
        <h1 className="mt-2 font-display text-3xl">Freelancer submission</h1>
        <p className="mt-1 text-slate-600">
          Upload PDF, PNG, or JPG files and describe the completed work.
        </p>
      </div>

      <form className="card space-y-4 p-6" onSubmit={onSubmit}>
        <div>
          <label className="label" htmlFor="files">
            Files
          </label>
          <input
            id="files"
            className="input"
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => setFiles(Array.from(e.target.files || []))}
          />
        </div>
        <div>
          <label className="label" htmlFor="description">
            Submission description
          </label>
          <textarea
            id="description"
            className="input min-h-32"
            minLength={10}
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        {task?.submission?.uploaded_files?.length ? (
          <p className="text-sm text-slate-500">
            Previously uploaded: {task.submission.uploaded_files.map((file) => file.file_name).join(", ")}
          </p>
        ) : null}
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary" disabled={busy}>
          {busy ? "Submitting…" : "Submit work"}
        </button>
      </form>
    </div>
  );
}

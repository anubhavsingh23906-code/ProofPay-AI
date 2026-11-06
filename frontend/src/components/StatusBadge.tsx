const styles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  agreement_pending: "bg-amber-100 text-amber-800",
  revision_requested: "bg-orange-100 text-orange-800",
  approved: "bg-sky-100 text-sky-800",
  submitted: "bg-indigo-100 text-indigo-800",
  verification_completed: "bg-violet-100 text-violet-800",
  client_accepted: "bg-emerald-100 text-emerald-800",
  paid: "bg-navy-900 text-white",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${
        styles[status] || "bg-slate-100 text-slate-700"
      }`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}

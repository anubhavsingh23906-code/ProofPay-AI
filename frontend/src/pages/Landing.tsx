import { Link } from "react-router-dom";

const steps = [
  {
    title: "Create a task",
    text: "Describe the work, INR budget, and deadline. The budget stays in INR and is never overwritten.",
  },
  {
    title: "Confirm an AI draft",
    text: "ProofPay drafts an agreement from the task. You review deliverables and acceptance criteria before work starts.",
  },
  {
    title: "Submit and verify",
    text: "The freelancer uploads files. AI compares evidence against the agreement and recommends accept, revision, or manual review.",
  },
  {
    title: "Client decides, then test checkout",
    text: "The client makes the final call. PayPal Sandbox then runs a USD 1.00 technical test payment — not escrow, and not the INR budget.",
  },
];

const features = [
  "Structured freelance agreements",
  "File uploads with PDF text extraction",
  "Advisory AI work verification",
  "PayPal Sandbox buyer approval and capture",
];

export default function Landing() {
  return (
    <div className="-mx-4 -my-8 overflow-hidden rounded-none bg-navy-950 text-white">
      <section className="mx-auto max-w-6xl px-4 py-20">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-300">
          PayPal AI Hackathon
        </p>
        <h1 className="mt-4 max-w-3xl font-display text-4xl leading-tight sm:text-6xl">
          Proof before pay. Agreements, evidence, and a safe sandbox checkout.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-slate-300">
          ProofPay AI helps clients and freelancers agree on work, check submissions against
          that agreement, and only then start a PayPal Sandbox test payment. AI advises.
          Humans decide.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/dashboard" className="btn-primary bg-white text-navy-900 hover:bg-slate-100">
            Get started
          </Link>
          <Link
            to="/tasks/new"
            className="btn-secondary border-white/20 bg-transparent text-white hover:bg-white/10"
          >
            Create a task
          </Link>
        </div>
      </section>

      <section className="border-t border-white/10 bg-navy-900/60 py-16">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 md:grid-cols-4">
          {steps.map((step, index) => (
            <article key={step.title} className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-sky-300">0{index + 1}</p>
              <h2 className="mt-2 font-display text-xl">{step.title}</h2>
              <p className="mt-2 text-sm text-slate-300">{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="font-display text-3xl">Built for a clear freelance workflow</h2>
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {features.map((feature) => (
            <li key={feature} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              {feature}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

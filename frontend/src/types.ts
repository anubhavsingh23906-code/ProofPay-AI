export type TaskStatus =
  | "draft"
  | "agreement_pending"
  | "revision_requested"
  | "approved"
  | "submitted"
  | "verification_completed"
  | "client_accepted"
  | "paid";

export type Payment = {
  provider?: string;
  order_id?: string;
  capture_id?: string;
  status?: string;
  currency?: string;
  test_amount?: string;
  sandbox?: boolean;
  label?: string;
  original_budget_untouched?: boolean;
};

export type Agreement = {
  deliverables: string[];
  acceptance_criteria: string[];
  client_must_provide: string[];
  assumptions_or_questions: string[];
  revision_count: number;
};

export type Verification = {
  completed_requirements: string[];
  missing_requirements: string[];
  unclear_requirements: string[];
  feedback: string;
  recommendation: "accept" | "request_revision" | "manual_review";
};

export type TaskSummary = {
  task_id: string;
  title: string;
  description: string;
  budget: number;
  currency: string;
  deadline_days: number;
  status: TaskStatus | string;
  payment?: Payment | null;
};

export type Task = TaskSummary & {
  agreement?: Agreement | null;
  agreement_decision?: { approved: boolean; feedback?: string | null } | null;
  submission?: {
    submission_text?: string;
    file_names?: string[];
    uploaded_files?: { file_name: string; content_type?: string; size_bytes?: number }[];
  } | null;
  verification?: Verification | null;
  client_review?: { decision: string; feedback?: string | null } | null;
};

export type DashboardStats = {
  total_tasks: number;
  pending_agreements: number;
  submitted_work: number;
  completed_tasks: number;
  payment_status: {
    none: number;
    created: number;
    approved: number;
    completed: number;
  };
};

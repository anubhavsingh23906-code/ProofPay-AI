import axios from "axios";
import type { DashboardStats, Task, TaskSummary } from "./types";

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const API_BASE = configuredApiUrl
  ? configuredApiUrl.replace(/\/$/, "")
  : import.meta.env.DEV
    ? "/api"
    : "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg || JSON.stringify(item)).join(" ");
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}

export async function getHealth() {
  const { data } = await api.get("/health");
  return data as { status: string; ollama?: string };
}

export async function getDashboard() {
  const { data } = await api.get("/dashboard");
  return data as DashboardStats;
}

export async function listTasks() {
  const { data } = await api.get("/tasks");
  return data as TaskSummary[];
}

export async function getTask(taskId: string) {
  const { data } = await api.get(`/tasks/${taskId}`);
  return data as Task;
}

export async function createTask(payload: {
  title: string;
  description: string;
  budget: number;
  currency: "INR";
  deadline_days: number;
}) {
  const { data } = await api.post("/tasks", payload);
  return data as TaskSummary;
}

export async function generateAgreement(taskId: string) {
  const { data } = await api.post(`/tasks/${taskId}/generate-agreement`);
  return data;
}

export async function approveAgreement(
  taskId: string,
  payload: { approved: boolean; feedback?: string },
) {
  const { data } = await api.post(`/tasks/${taskId}/approve-agreement`, payload);
  return data;
}

export async function uploadFiles(taskId: string, files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const { data } = await api.post(`/tasks/${taskId}/upload-files`, form);
  return data;
}

export async function submitWork(
  taskId: string,
  payload: { submission_text: string; file_names: string[] },
) {
  const { data } = await api.post(`/tasks/${taskId}/submit-work`, payload);
  return data;
}

export async function verifyWork(taskId: string) {
  const { data } = await api.post(`/tasks/${taskId}/verify-work`);
  return data;
}

export async function reviewWork(
  taskId: string,
  payload: { decision: "accept" | "request_revision"; feedback?: string },
) {
  const { data } = await api.post(`/tasks/${taskId}/review-verification`, payload);
  return data;
}

export async function createPayment(taskId: string) {
  const { data } = await api.post(`/tasks/${taskId}/create-payment`);
  return data as {
    approval_url: string;
    payment: Task["payment"];
    notice?: string;
    message: string;
  };
}

export async function capturePayment(taskId: string, orderId?: string) {
  const { data } = await api.post(`/tasks/${taskId}/capture-payment`, {
    order_id: orderId,
  });
  return data;
}

export async function getPayment(taskId: string) {
  const { data } = await api.get(`/tasks/${taskId}/payment`);
  return data;
}

import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import CreateTask from "./pages/CreateTask";
import TaskDetails from "./pages/TaskDetails";
import SubmitWork from "./pages/SubmitWork";
import Verification from "./pages/Verification";
import ClientReview from "./pages/ClientReview";
import Payment from "./pages/Payment";
import PaymentSuccess from "./pages/PaymentSuccess";
import PaymentCancel from "./pages/PaymentCancel";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/tasks/new" element={<CreateTask />} />
        <Route path="/tasks/:taskId" element={<TaskDetails />} />
        <Route path="/tasks/:taskId/submit" element={<SubmitWork />} />
        <Route path="/tasks/:taskId/verify" element={<Verification />} />
        <Route path="/tasks/:taskId/review" element={<ClientReview />} />
        <Route path="/tasks/:taskId/pay" element={<Payment />} />
        <Route path="/payment/success" element={<PaymentSuccess />} />
        <Route path="/payment/cancel" element={<PaymentCancel />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

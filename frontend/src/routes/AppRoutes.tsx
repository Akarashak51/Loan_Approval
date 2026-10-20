import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import ProtectedRoute from '../components/common/ProtectedRoute';

const Landing = lazy(() => import('../pages/Landing/Landing'));
const Login = lazy(() => import('../pages/Login/Login'));
const GoogleCallback = lazy(() => import('../pages/Login/GoogleCallback'));
const Register = lazy(() => import('../pages/Register/Register'));
const Application = lazy(() => import('../pages/Application/Application'));
const Results = lazy(() => import('../pages/Results/Results'));
const History = lazy(() => import('../pages/History/History'));
const Profile = lazy(() => import('../pages/Profile/Profile'));
const Admin = lazy(() => import('../pages/Admin/Admin'));
const Status = lazy(() => import('../pages/Status/Status'));
const Insights = lazy(() => import('../pages/Insights/Insights'));
const Settings = lazy(() => import('../pages/Settings/Settings'));
const About = lazy(() => import('../pages/About/About'));
const MerchantRisk = lazy(() => import('../pages/MerchantRisk/MerchantRisk'));
const Portfolio = lazy(() => import('../pages/Portfolio/Portfolio'));
const RiskAnalysis = lazy(() => import('../pages/RiskAnalysis/RiskAnalysis'));
const CreditAnalytics = lazy(() => import('../pages/Analytics/CreditAnalytics'));
const Reports = lazy(() => import('../pages/Reports/Reports'));
const ReviewQueue = lazy(() => import('../pages/Admin/ReviewQueue'));
const ModelOps = lazy(() => import('../pages/Admin/ModelOps'));
const DocumentVerification = lazy(() => import('../pages/Admin/DocumentVerification'));
const DocumentVerificationSection = lazy(() => import('../components/forms/DocumentVerificationSection'));

export default function AppRoutes() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-600" role="status">Loading page…</div>}>
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<ProtectedRoute><Landing /></ProtectedRoute>} />
        <Route path="/login" element={<Login />} />
        <Route path="/auth/google/callback" element={<GoogleCallback />} />
        <Route path="/register" element={<Register />} />
        <Route path="/apply" element={<ProtectedRoute allowedRoles={['applicant']}><Application /></ProtectedRoute>} />
        <Route path="/documents" element={<ProtectedRoute allowedRoles={['applicant']}><DocumentVerificationSection /></ProtectedRoute>} />
        <Route path="/merchant-risk" element={<ProtectedRoute allowedRoles={['admin', 'loan_officer']}><MerchantRisk /></ProtectedRoute>} />
        <Route path="/portfolio" element={<ProtectedRoute allowedRoles={['admin', 'loan_officer']}><Portfolio /></ProtectedRoute>} />
        <Route path="/results/:id" element={<ProtectedRoute><Results /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute allowedRoles={['applicant']}><History /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/status" element={<ProtectedRoute allowedRoles={['applicant']}><Status /></ProtectedRoute>} />
        <Route path="/insights" element={<ProtectedRoute allowedRoles={['applicant']}><Insights /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/about" element={<ProtectedRoute><About /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute allowedRoles={['admin', 'loan_officer']}><CreditAnalytics /></ProtectedRoute>} />
        <Route path="/risk-analysis" element={<ProtectedRoute allowedRoles={['admin', 'loan_officer']}><RiskAnalysis /></ProtectedRoute>} />
        <Route path="/reports" element={<ProtectedRoute allowedRoles={['admin', 'loan_officer']}><Reports /></ProtectedRoute>} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Admin />
            </ProtectedRoute>
          }
        />
        <Route path="/admin/review" element={<ProtectedRoute allowedRoles={['admin']}><ReviewQueue /></ProtectedRoute>} />
        <Route path="/admin/model-ops" element={<ProtectedRoute allowedRoles={['admin']}><ModelOps /></ProtectedRoute>} />
        <Route path="/admin/documents" element={<ProtectedRoute allowedRoles={['admin']}><DocumentVerification /></ProtectedRoute>} />
      </Route>
    </Routes>
    </Suspense>
  );
}

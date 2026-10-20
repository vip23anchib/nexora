import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Schemas } from './pages/Schemas';
import { Ingestion } from './pages/Ingestion';
import { Records } from './pages/Records';
import { AuditTrail } from './pages/AuditTrail';
import { Team } from './pages/Team';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="schemas" element={<Schemas />} />
            <Route path="ingestion" element={<Ingestion />} />
            <Route path="records" element={<Records />} />
            <Route path="audit" element={<AuditTrail />} />
            <Route path="team" element={<Team />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

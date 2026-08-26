import { createBrowserRouter, Navigate } from 'react-router-dom';
import LandingPage from '@/landing/LandingPage';
import AppLayout from '@/app/AppLayout';
import DashboardPage from '@/app/pages/DashboardPage';
import AgendaPage from '@/app/pages/AgendaPage';
import InboxPage from '@/app/pages/InboxPage';
import ClientesPage from '@/app/pages/ClientesPage';
import CadastrosPage from '@/app/pages/CadastrosPage';
import FinanceiroPage from '@/app/pages/FinanceiroPage';
import TokensPage from '@/app/pages/TokensPage';

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  {
    path: '/app',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="agenda" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'agenda', element: <AgendaPage /> },
      { path: 'conversas', element: <InboxPage /> },
      { path: 'clientes', element: <ClientesPage /> },
      { path: 'cadastros', element: <CadastrosPage /> },
      { path: 'financeiro', element: <FinanceiroPage /> },
      { path: 'tokens', element: <TokensPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);

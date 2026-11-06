import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AcceptInviteScreen, LoginScreen, RequireAuth } from '@/features/auth';
import { InboxScreen } from '@/features/conversations';
import { CustomersScreen } from '@/features/customers';
import { DashboardScreen } from '@/features/dashboard';
import { TokensScreen } from '@/features/design-system';
import { FinanceScreen } from '@/features/finance';
import { LandingScreen } from '@/features/landing';
import { RegistryScreen } from '@/features/registry';
import { AgendaScreen } from '@/features/scheduling';
import AppLayout from './_shell/AppLayout';

/** Every route renders a screen through its feature's barrel (`features/<f>/index.ts`). */
export const router = createBrowserRouter([
  { path: '/', element: <LandingScreen /> },
  { path: '/entrar', element: <LoginScreen /> },
  { path: '/convite/:token', element: <AcceptInviteScreen /> },
  {
    // Everything under /app requires a session; RequireAuth sends anonymous
    // visitors to /entrar and remembers where they were going.
    element: <RequireAuth />,
    children: [
      {
        path: '/app',
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="agenda" replace /> },
          { path: 'dashboard', element: <DashboardScreen /> },
          { path: 'agenda', element: <AgendaScreen /> },
          { path: 'conversas', element: <InboxScreen /> },
          { path: 'clientes', element: <CustomersScreen /> },
          { path: 'cadastros', element: <RegistryScreen /> },
          { path: 'financeiro', element: <FinanceScreen /> },
          { path: 'tokens', element: <TokensScreen /> },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);

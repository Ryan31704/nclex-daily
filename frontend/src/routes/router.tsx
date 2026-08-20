import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { GuestOnlyRoute, ProtectedRoute } from '../features/auth/RouteGuards'
import { LandingPage } from '../pages/LandingPage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    element: <GuestOnlyRoute />,
    children: [
      {
        path: '/login',
        element: <LoginPage />,
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            path: '/dashboard',
            lazy: async () => {
              const { DashboardPage } = await import('../pages/DashboardPage')
              return { Component: DashboardPage }
            },
          },
          {
            path: '/progress',
            lazy: async () => {
              const { ProgressPage } = await import('../pages/ProgressPage')
              return { Component: ProgressPage }
            },
          },
          {
            path: '/topics/:slug',
            lazy: async () => {
              const { TopicPage } = await import('../pages/TopicPage')
              return { Component: TopicPage }
            },
          },
          {
            path: '/practice',
            lazy: async () => {
              const { PracticeStartPage } = await import('../pages/PracticeStartPage')
              return { Component: PracticeStartPage }
            },
          },
          {
            path: '/review',
            lazy: async () => {
              const { ReviewPage } = await import('../pages/ReviewPage')
              return { Component: ReviewPage }
            },
          },
          {
            path: '/profile',
            lazy: async () => {
              const { ProfilePage } = await import('../pages/ProfilePage')
              return { Component: ProfilePage }
            },
          },
        ],
      },
      {
        path: '/practice/:sessionId',
        lazy: async () => {
          const { PracticePage } = await import('../pages/PracticePage')
          return { Component: PracticePage }
        },
      },
      {
        path: '/practice/:sessionId/complete',
        lazy: async () => {
          const { SessionCompletePage } = await import('../pages/SessionCompletePage')
          return { Component: SessionCompletePage }
        },
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider } from './contexts/AuthContext'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfirmDialogProvider } from './components/ui/confirm-dialog'
import { Toaster } from '@/components/ui/sonner'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import UsersPage from './pages/UsersPage'
import CoursesPage from './pages/CoursesPage'
import EventsPage from './pages/EventsPage'
import EventDetailPage from './pages/EventDetailPage'
import ParticipantsPage from './pages/ParticipantsPage'
import LiveScorePage from './pages/LiveScorePage' // Phase 3.2: Public Live Score
import WinnerPage from './pages/WinnerPage' // Phase 3.3: Public Winner Display
import ProtectedRoute from './components/auth/ProtectedRoute'
import Layout from './components/layout/Layout'
import { startTokenMonitoring } from './utils/tokenMonitor'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  // Start token monitoring on app initialization if user is logged in
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      console.log('App initialized with token, starting token monitor...')
      startTokenMonitoring()
    }
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ConfirmDialogProvider>
          <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              {/* Phase 3.2: Public Live Score Page (no auth required) */}
              <Route path="/live-score/:eventId" element={<LiveScorePage />} />
              {/* Phase 3.3: Public Winner Page (no auth required) */}
              <Route path="/winners/:eventId" element={<WinnerPage />} />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/users" element={<UsersPage />} />
                        <Route path="/courses" element={<CoursesPage />} />
                        <Route path="/events" element={<EventsPage />} />
                        <Route path="/events/:id" element={<EventDetailPage />} />
                        <Route path="/participants" element={<ParticipantsPage />} />
                      </Routes>
                    </Layout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Router>
          <Toaster />
        </ConfirmDialogProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App

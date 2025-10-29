import { useAuth } from '@/contexts/AuthContext'
import { Link, useLocation } from 'react-router-dom'
import { usePermissions } from '@/hooks/usePermissions'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth()
  const { canManageUsers } = usePermissions()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', current: location.pathname === '/dashboard' },
    ...(canManageUsers() ? [{ name: 'Users', href: '/users', current: location.pathname === '/users' }] : []),
    { name: 'Courses', href: '/courses', current: location.pathname === '/courses' },
    { name: 'Events', href: '/events', current: location.pathname === '/events' || location.pathname.startsWith('/events/') },
  ]

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Navigation */}
      <nav className="bg-orange-500 shadow-lg border-b border-orange-600 flex-shrink-0">
        <div className="px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="h-10 w-10 bg-white rounded-xl flex items-center justify-center mr-4 shadow-lg">
                  <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21l18-9L3 3v18z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21l6-6" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 15l6-6" />
                    <circle cx="18" cy="6" r="2" fill="currentColor" />
                  </svg>
                </div>
                <h1 className="text-xl font-bold text-white">
                  Abhimata Golf Management
                </h1>
              </div>
              <div className="ml-12 flex space-x-8">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      item.current
                        ? 'border-white text-white'
                        : 'border-transparent text-orange-100 hover:text-white hover:border-orange-200'
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors`}
                  >
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center">
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-white rounded-full flex items-center justify-center">
                    <span className="text-orange-600 font-semibold text-sm">
                      {user?.full_name?.charAt(0) || 'U'}
                    </span>
                  </div>
                  <div className="text-sm">
                    <div className="font-medium text-white">{user?.full_name}</div>
                    <div className="text-orange-100 capitalize">{user?.role.replace('_', ' ')}</div>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="bg-white hover:bg-orange-50 text-orange-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-orange-200 hover:border-orange-300 hover:shadow-md"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content - takes remaining height */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  )
}

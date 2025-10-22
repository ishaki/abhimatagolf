import { useNavigate } from 'react-router-dom'
import UpcomingEventsList from '@/components/dashboard/UpcomingEventsList'
import { usePermissions } from '@/hooks/usePermissions'

export default function Dashboard() {
  const navigate = useNavigate()
  const { canManageUsers, canManageCourses, canCreateEvents } = usePermissions()

  return (
    <div className="h-screen w-screen overflow-hidden bg-gray-50 flex flex-col">
      {/* Main content area - single section layout */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="min-h-full flex flex-col space-y-8">
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
            {/* Quick Actions - Compact */}
            <div className="xl:col-span-1">
              <div className="bg-white rounded-xl shadow-lg p-4 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  {canCreateEvents() && (
                    <button
                      onClick={() => navigate('/events')}
                      className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-all duration-200 border border-blue-200 hover:border-blue-300 hover:shadow-md group"
                    >
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center mr-3 shadow-sm group-hover:shadow-md transition-shadow">
                          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 text-sm">Create Event</div>
                          <div className="text-xs text-gray-600">New tournament</div>
                        </div>
                      </div>
                    </button>
                  )}
                  {canManageCourses() && (
                    <button
                      onClick={() => navigate('/courses', { state: { openForm: true } })}
                      className="w-full text-left p-3 bg-orange-50 hover:bg-orange-100 rounded-lg transition-all duration-200 border border-orange-200 hover:border-orange-300 hover:shadow-md group"
                    >
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center mr-3 shadow-sm group-hover:shadow-md transition-shadow">
                          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          </svg>
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 text-sm">Add Course</div>
                          <div className="text-xs text-gray-600">New golf course</div>
                        </div>
                      </div>
                    </button>
                  )}
                  {canManageUsers() && (
                    <button
                      onClick={() => navigate('/users')}
                      className="w-full text-left p-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-all duration-200 border border-purple-200 hover:border-purple-300 hover:shadow-md group"
                    >
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center mr-3 shadow-sm group-hover:shadow-md transition-shadow">
                          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                          </svg>
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 text-sm">Manage Users</div>
                          <div className="text-xs text-gray-600">User accounts</div>
                        </div>
                      </div>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Upcoming Events - More Space */}
            <div className="xl:col-span-3">
              <UpcomingEventsList />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

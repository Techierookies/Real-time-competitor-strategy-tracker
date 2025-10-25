import { Search, Bell } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const AdminHeader = () => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Search:', searchQuery);
  };

  // Dummy notifications for display
  const notifications = [
    { id: 1, message: 'New order placed', createdAt: new Date(), read: false },
    { id: 2, message: 'Product stock updated', createdAt: new Date(), read: true },
  ];

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAsRead = (id: number) => {
    console.log('Marked as read:', id);
  };

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-white border-b border-gray-200 z-40 transition-all shadow-sm">
      <div className="h-full px-6 flex items-center justify-between">
        
        {/* Left Section - Greeting and Search */}
        <div className="flex-1 flex items-center gap-6">
          <div>
            <h2 className="text-lg font-semibold text-black">
              Welcome back, <span className="text-blue-600">{user?.name?.split(' ')[0] || 'Admin'}</span>
            </h2>
            <p className="text-sm text-gray-600">{today}</p>
          </div>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search products, orders, users..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </form>
        </div>

        {/* Right Section - Notifications & Avatar */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
              aria-label="Notifications"
            >
              <Bell className="text-gray-800" size={20} />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-semibold text-black">Notifications</h3>
                </div>
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">No notifications</div>
                ) : (
                  <ul>
                    {notifications.map((notif) => (
                      <li
                        key={notif.id}
                        onClick={() => markAsRead(notif.id)}
                        className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                          !notif.read ? 'bg-blue-50' : ''
                        }`}
                      >
                        <p className="text-sm text-black">{notif.message}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(notif.createdAt).toLocaleTimeString('en-IN')}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* User Avatar */}
          <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center shadow-md">
            <span className="text-sm font-semibold text-white">
              {user?.name?.charAt(0)?.toUpperCase() || 'A'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

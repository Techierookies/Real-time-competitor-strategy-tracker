import { Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';
import { AdminHeader } from './AdminHeader';

export const AdminLayout = () => {
  return (
    <div className="min-h-screen bg-white text-black transition-colors">
      {/* Sidebar */}
      <AdminSidebar />

      {/* Main content area */}
      <div className="ml-64 flex flex-col min-h-screen">
        {/* Fixed Header */}
        <div className="fixed top-0 left-64 right-0 z-10 bg-white border-b border-gray-200 shadow-sm">
          <AdminHeader />
        </div>

        {/* Page Content */}
        <main className="flex-1 mt-16 p-6 bg-gray-50 text-black">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

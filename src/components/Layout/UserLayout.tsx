import { Outlet } from 'react-router-dom';
import { UserNavbar } from './UserNavbar';
import { UserBottomNav } from './UserBottomNav';

export const UserLayout = () => {
  return (
    <div className="min-h-screen bg-background">
      <UserNavbar />
      <main className="pb-16 md:pb-0">
        <Outlet />
      </main>
      <UserBottomNav />
    </div>
  );
};
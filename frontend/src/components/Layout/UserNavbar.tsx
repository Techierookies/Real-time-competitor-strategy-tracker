import { Link, useLocation } from 'react-router-dom';
import { Search, ShoppingCart, User } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useAuth } from '../../contexts/AuthContext';

export const UserNavbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navLinks = [
    { to: '/products', label: 'Products' },
    { to: '/cart', label: 'Cart' },
    { to: '/support', label: 'Support' },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm transition-all">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo / Brand */}
        <Link to="/" className="font-display text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors">
          iPhone<span className="text-blue-600">Store</span>
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-8">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`text-sm font-medium transition-colors ${
                location.pathname === to
                  ? 'text-blue-600 border-b-2 border-blue-600 pb-1'
                  : 'text-gray-700 hover:text-blue-600'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        {/* Icons & User Controls */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            className="hover:bg-blue-50 text-gray-700 hover:text-blue-600"
          >
            <Search className="h-5 w-5" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="hover:bg-blue-50 text-gray-700 hover:text-blue-600 relative"
          >
            <ShoppingCart className="h-5 w-5" />
            {/* Example cart badge */}
            <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-xs w-4 h-4 flex items-center justify-center rounded-full">
              2
            </span>
          </Button>

          {user ? (
            <div className="flex items-center space-x-2">
              <span className="hidden md:inline text-sm text-gray-600">
                Hi, {user.name.split(' ')[0]}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                className="hover:bg-blue-50 text-gray-700 hover:text-blue-600"
              >
                <User className="h-5 w-5" />
              </Button>
            </div>
          ) : (
            <Link to="/login">
              <Button
                variant="ghost"
                size="icon"
                className="hover:bg-blue-50 text-gray-700 hover:text-blue-600"
              >
                <User className="h-5 w-5" />
              </Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

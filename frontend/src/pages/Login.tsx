import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import { Eye, EyeOff, Shield, User } from 'lucide-react';

export const Login = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const success = await login(email, password, isAdmin);
      if (success) {
        toast({
          title: "Welcome back!",
          description: `Logged in as ${isAdmin ? 'admin' : 'user'} successfully.`,
        });
        navigate(isAdmin ? '/admin' : '/');
      } else {
        toast({
          title: "Login failed",
          description: "Please check your credentials and try again.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-pink-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-block">
            <h1 className="font-display text-3xl font-bold bg-gradient-to-r from-indigo-600 to-pink-600 bg-clip-text text-transparent">
              iPhone Store
            </h1>
          </Link>
          <p className="text-sm text-gray-500 mt-1">Your premium Apple shopping experience</p>
        </div>

        {/* Login Type Toggle */}
        <div className="flex bg-gray-100 rounded-xl p-1 mb-6 shadow-inner">
          <button
            type="button"
            onClick={() => setIsAdmin(false)}
            className={`flex-1 flex items-center justify-center space-x-2 py-2 px-3 rounded-lg transition-all ${
              !isAdmin ? 'bg-white shadow text-indigo-600 font-medium' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <User className="h-4 w-4" />
            <span>User</span>
          </button>
          
          <button
            type="button"
            onClick={() => setIsAdmin(true)}
            className={`flex-1 flex items-center justify-center space-x-2 py-2 px-3 rounded-lg transition-all ${
              isAdmin ? 'bg-white shadow text-indigo-600 font-medium' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Shield className="h-4 w-4" />
            <span>Admin</span>
          </button>
        </div>

        {/* Login Card */}
        <Card className="backdrop-blur-xl bg-white/70 shadow-2xl border border-white/30 rounded-2xl">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto w-14 h-14 bg-gradient-to-r from-indigo-200 to-pink-200 rounded-full flex items-center justify-center shadow-md">
              {isAdmin ? (
                <Shield className="h-7 w-7 text-indigo-600" />
              ) : (
                <User className="h-7 w-7 text-indigo-600" />
              )}
            </div>
            <CardTitle className="font-display text-2xl">
              {isAdmin ? 'Admin Login' : 'Welcome Back'}
            </CardTitle>
            <CardDescription className="text-gray-600">
              {isAdmin 
                ? 'Access your admin dashboard securely'
                : 'Sign in to continue your shopping journey'}
            </CardDescription>
          </CardHeader>

          <CardContent className="p-6">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div>
                <Label htmlFor="email" className="text-gray-700">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="rounded-xl mt-1 border-gray-300 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Password */}
              <div>
                <Label htmlFor="password" className="text-gray-700">Password</Label>
                <div className="relative mt-1">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="rounded-xl pr-10 border-gray-300 focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-indigo-600 to-pink-600 text-white py-3 rounded-xl font-medium shadow-md hover:opacity-90 transition"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : `Sign in ${isAdmin ? 'as Admin' : ''}`}
              </Button>
            </form>

            {/* Signup Redirect */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Don’t have an account?{' '}
                <Link to="/signup" className="text-indigo-600 hover:underline font-medium">
                  Sign up
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

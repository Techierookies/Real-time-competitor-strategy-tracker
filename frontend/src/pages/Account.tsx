import { useAuth } from "../contexts/AuthContext";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import {
  User,
  Mail,
  Phone,
  MapPin,
  CreditCard,
  Package,
  Settings,
  LogOut,
  ShoppingBag,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export const Account = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-20">
        <Card className="max-w-md mx-auto p-10 text-center backdrop-blur-lg bg-white/40 border border-gray-200 shadow-lg">
          <User className="h-16 w-16 text-gray-500 mx-auto mb-4" />
          <h2 className="font-display text-4xl font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent mb-3">
            Please Sign In
          </h2>
          <p className="text-muted-foreground mb-6">
            Sign in to access your account and order history.
          </p>
          <Button
            onClick={() => navigate("/login")}
            className="bg-black text-white hover:bg-gray-800 rounded-full px-8 py-2"
          >
            Sign In
          </Button>
        </Card>
      </div>
    );
  }

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const formatINR = (price: number) =>
    price.toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    });

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="max-w-5xl mx-auto space-y-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display text-4xl md:text-5xl font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent">
              My Account
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Welcome back, <span className="font-medium">{user.name.split(" ")[0]}</span> 👋
            </p>
          </div>
          <Button
            variant="outline"
            onClick={handleLogout}
            className="rounded-full border-gray-300 hover:bg-red-500 hover:text-white transition-all duration-300"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>

        <div className="grid lg:grid-cols-3 gap-10">
          {/* Account Overview */}
          <div className="lg:col-span-2 space-y-8">
            {/* Personal Information */}
            <Card className="p-6 backdrop-blur-md bg-white/70 border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-display text-2xl font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent">
                  Personal Information
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-full hover:bg-indigo-50"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <Label htmlFor="firstName">First Name</Label>
                  <Input id="firstName" value={user.name.split(" ")[0]} readOnly />
                </div>
                <div>
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input id="lastName" value={user.name.split(" ")[1] || ""} readOnly />
                </div>
                <div className="md:col-span-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" value={user.email} readOnly />
                </div>
              </div>
            </Card>

            {/* Recent Orders */}
            <Card className="p-6 backdrop-blur-md bg-white/70 border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300">
              <h2 className="font-display text-2xl font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent mb-6">
                Recent Orders
              </h2>

              <div className="space-y-4">
                {/* Order 1 */}
                <div className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all duration-300">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-indigo-100 rounded-lg">
                      <Package className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">iPhone 15 Pro Max</p>
                      <p className="text-sm text-muted-foreground">Order #IP2024001</p>
                      <p className="text-xs text-muted-foreground">Placed on Jan 15, 2024</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className="bg-green-100 text-green-700 mb-1">Delivered</Badge>
                    <p className="text-sm font-medium text-foreground">
                      {formatINR(140900)}
                    </p>
                  </div>
                </div>

                {/* Order 2 */}
                <div className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all duration-300">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Package className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">iPhone 15</p>
                      <p className="text-sm text-muted-foreground">Order #IP2024002</p>
                      <p className="text-xs text-muted-foreground">Placed on Jan 20, 2024</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className="bg-blue-100 text-blue-700 mb-1">Shipped</Badge>
                    <p className="text-sm font-medium text-foreground">
                      {formatINR(79900)}
                    </p>
                  </div>
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full mt-6 rounded-full hover:bg-gray-100 transition-all"
              >
                <ShoppingBag className="h-4 w-4 mr-2" />
                View All Orders
              </Button>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="space-y-8">
            {/* Account Stats */}
            <Card className="p-6 backdrop-blur-md bg-white/70 border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300">
              <h3 className="font-display text-xl font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent mb-4">
                Account Stats
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Orders</span>
                  <span className="font-medium text-foreground">2</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Spent</span>
                  <span className="font-medium text-foreground">
                    {formatINR(140900 + 79900)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Member Since</span>
                  <span className="font-medium text-foreground">Jan 2024</span>
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6 backdrop-blur-md bg-white/70 border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300">
              <h3 className="font-display text-xl font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <Button variant="outline" className="w-full justify-start rounded-full hover:bg-indigo-50">
                  <MapPin className="h-4 w-4 mr-2" />
                  Manage Addresses
                </Button>
                <Button variant="outline" className="w-full justify-start rounded-full hover:bg-indigo-50">
                  <CreditCard className="h-4 w-4 mr-2" />
                  Payment Methods
                </Button>
                <Button variant="outline" className="w-full justify-start rounded-full hover:bg-indigo-50">
                  <Mail className="h-4 w-4 mr-2" />
                  Email Preferences
                </Button>
                <Button variant="outline" className="w-full justify-start rounded-full hover:bg-indigo-50">
                  <Phone className="h-4 w-4 mr-2" />
                  Contact Support
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

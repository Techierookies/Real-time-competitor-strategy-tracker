import { useState } from "react";
import { Ban, CheckCircle, Mail, Phone, UserCog } from "lucide-react";
import { useToast } from "../../hooks/use-toast";
import { Input } from "../../components/ui/input";
import { Card, CardContent, CardHeader } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";

interface User {
  id: string;
  name: string;
  email: string;
  role: "customer" | "admin" | "manager";
  status: "active" | "banned";
  joinedDate: string;
  totalOrders: number;
  totalSpent: number;
}

export const AdminUsers = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const [users, setUsers] = useState<User[]>([
    { id: "1", name: "Amit Patel", email: "amit@example.com", role: "customer", status: "active", joinedDate: "2024-01-10", totalOrders: 6, totalSpent: 56900 },
    { id: "2", name: "Rajesh Kumar", email: "rajesh@example.com", role: "customer", status: "active", joinedDate: "2024-01-12", totalOrders: 8, totalSpent: 32400 },
    { id: "3", name: "Priya Sharma", email: "priya@example.com", role: "customer", status: "banned", joinedDate: "2024-01-05", totalOrders: 3, totalSpent: 1200 },
    { id: "4", name: "Sneha Reddy", email: "sneha@example.com", role: "customer", status: "active", joinedDate: "2023-12-01", totalOrders: 0, totalSpent: 0 },
    { id: "5", name: "Priyanshi Agarwal", email: "priyanshi@example.com", role: "customer", status: "active", joinedDate: "2024-01-20", totalOrders: 15, totalSpent: 8940 },
  ]);

  const toggleUserStatus = (userId: string) => {
    setUsers(
      users.map((user) => {
        if (user.id === userId) {
          const newStatus = user.status === "active" ? "banned" : "active";
          toast({
            title: `User ${newStatus === "banned" ? "banned" : "unbanned"}`,
            description: `${user.name} has been ${newStatus === "banned" ? "banned" : "unbanned"} successfully.`,
          });
          return { ...user, status: newStatus };
        }
        return user;
      })
    );
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "all" || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-primary">Users</h1>
          <p className="text-foreground/60 mt-1">Manage user accounts and permissions</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Input
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full sm:w-64"
          />
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="border rounded-md p-2 text-sm text-gray-700"
          >
            <option value="all">All Roles</option>
            <option value="customer">Customers</option>
            <option value="manager">Managers</option>
            <option value="admin">Admins</option>
          </select>
        </div>
      </div>

      {/* Users Grid */}
      <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {filteredUsers.map((user) => (
          <Card
            key={user.id}
            className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-300"
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
                    {user.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{user.name}</h3>
                    <Badge
                      variant={
                        user.status === "active"
                          ? "default"
                          : "destructive"
                      }
                    >
                      {user.status}
                    </Badge>
                  </div>
                </div>
                <Badge variant={user.role === "customer" ? "secondary" : "outline"}>
                  {user.role}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="text-sm text-gray-600 space-y-2">
                <div className="flex items-center gap-2">
                  <Mail size={16} /> <span>{user.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone size={16} /> <span>+91-98XXX-XXXX</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-gray-50 rounded-lg p-3">
                <div>
                  <p className="text-xs text-gray-500">Total Orders</p>
                  <p className="text-lg font-semibold text-gray-800">{user.totalOrders}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Total Spent</p>
                  <p className="text-lg font-semibold text-gray-800">₹{user.totalSpent.toLocaleString()}</p>
                </div>
              </div>

              <p className="text-xs text-gray-500">Joined on {user.joinedDate}</p>

              <div className="flex justify-between items-center">
                <div className="flex gap-2">
                  <Button variant="ghost" size="icon" title="Manage role">
                    <UserCog className="h-4 w-4 text-gray-600" />
                  </Button>
                  <Button variant="ghost" size="icon" title="Send email">
                    <Mail className="h-4 w-4 text-gray-600" />
                  </Button>
                </div>
                <Button
                  onClick={() => toggleUserStatus(user.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    user.status === "active"
                      ? "bg-red-50 text-red-600 hover:bg-red-100"
                      : "bg-green-50 text-green-600 hover:bg-green-100"
                  }`}
                >
                  {user.status === "active" ? (
                    <div className="flex items-center gap-2">
                      <Ban size={16} /> Ban
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} /> Unban
                    </div>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

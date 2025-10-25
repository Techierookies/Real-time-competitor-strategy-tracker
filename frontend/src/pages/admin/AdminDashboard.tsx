import {
    TrendingUp,
    TrendingDown,
    Users,
    DollarSign,
    Smartphone,
    AlertCircle,
    Package,
  } from 'lucide-react';

  import { Button } from '../../components/ui/button';
  
  export const AdminDashboard = () => {
    const stats = [
      {
        title: 'Total Revenue',
        value: '₹2,34,56,789',
        change: '+12.5%',
        trend: 'up',
        icon: DollarSign,
        color: 'bg-green-500',
      },
      {
        title: 'iPhones Sold',
        value: '3,247',
        change: '+8.2%',
        trend: 'up',
        icon: Smartphone,
        color: 'bg-blue-500',
      },
      {
        title: 'Active Users',
        value: '12,847',
        change: '+5.1%',
        trend: 'up',
        icon: Users,
        color: 'bg-purple-500',
      },
      {
        title: 'Conversion Rate',
        value: '3.47%',
        change: '-0.8%',
        trend: 'down',
        icon: TrendingDown,
        color: 'bg-orange-500',
      },
    ];
  
    const recentSales = [
      { customer: 'Rajesh Kumar', model: 'iPhone 15 Pro Max', amount: '₹99,990', time: '2 min ago', location: 'Mumbai' },
      { customer: 'Priya Sharma', model: 'iPhone 15 Pro', amount: '₹83,990', time: '5 min ago', location: 'Delhi' },
      { customer: 'Amit Patel', model: 'iPhone 15', amount: '₹66,990', time: '8 min ago', location: 'Bangalore' },
      { customer: 'Ananya Singh', model: 'iPhone 14', amount: '₹58,990', time: '12 min ago', location: 'Pune' },
    ];
  
    return (
      <div className="p-6 space-y-8 bg-white text-black min-h-screen">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard Overview</h1>
          <p className="text-gray-600">
            Monitor your iPhone store performance and insights.
          </p>
        </div>
  
        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="text-white" size={22} />
                </div>
                <span
                  className={`text-sm font-medium ${
                    stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stat.change}
                </span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</h3>
              <p className="text-sm text-gray-600">{stat.title}</p>
            </div>
          ))}
        </div>
  
        {/* Main Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Recent Sales */}
          <div className="lg:col-span-2 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Sales</h2>
            <div className="space-y-4">
              {recentSales.map((sale, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all"
                >
                  <div>
                    <p className="font-medium text-gray-900">{sale.customer}</p>
                    <p className="text-sm text-gray-600">
                      {sale.model} • {sale.location}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">{sale.amount}</p>
                    <p className="text-sm text-gray-500">{sale.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
  
          {/* AI Insights */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-bold flex items-center mb-4 text-gray-900">
              <AlertCircle className="h-5 w-5 mr-2 text-blue-500" />
              AI Insights
            </h2>
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                <p className="text-sm font-medium text-blue-700 mb-1">Price Alert</p>
                <p className="text-sm text-blue-600">
                  Samsung Galaxy S24 Ultra dropped 5% below your iPhone 15 Pro Max pricing.
                </p>
                <Button variant="ghost" size="sm" className="mt-2 text-blue-700 hover:text-blue-800">
                  View Details
                </Button>
              </div>
  
              <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                <p className="text-sm font-medium text-green-700 mb-1">Opportunity</p>
                <p className="text-sm text-green-600">
                  iPhone 14 demand increased 15% this week. Consider a promotional push.
                </p>
                <Button variant="ghost" size="sm" className="mt-2 text-green-700 hover:text-green-800">
                  Create Campaign
                </Button>
              </div>
  
              <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
                <p className="text-sm font-medium text-orange-700 mb-1">Stock Alert</p>
                <p className="text-sm text-orange-600">
                  iPhone 15 Pro Max Titanium running low. Restock recommended.
                </p>
                <Button variant="ghost" size="sm" className="mt-2 text-orange-700 hover:text-orange-800">
                  Order Stock
                </Button>
              </div>
            </div>
          </div>
        </div>
  
        {/* Quick Actions */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button className="h-24 flex-col space-y-2 bg-gray-50 border hover:bg-gray-100 transition">
              <Smartphone className="h-6 w-6 text-gray-700" />
              <span className="text-sm text-gray-800">Add Product</span>
            </Button>
            <Button className="h-24 flex-col space-y-2 bg-gray-50 border hover:bg-gray-100 transition">
              <TrendingUp className="h-6 w-6 text-gray-700" />
              <span className="text-sm text-gray-800">View Analytics</span>
            </Button>
            <Button className="h-24 flex-col space-y-2 bg-gray-50 border hover:bg-gray-100 transition">
              <Users className="h-6 w-6 text-gray-700" />
              <span className="text-sm text-gray-800">Manage Users</span>
            </Button>
            <Button className="h-24 flex-col space-y-2 bg-gray-50 border hover:bg-gray-100 transition">
              <Package className="h-6 w-6 text-gray-700" />
              <span className="text-sm text-gray-800">Notifications</span>
            </Button>
          </div>
        </div>
      </div>
    );
  };
  
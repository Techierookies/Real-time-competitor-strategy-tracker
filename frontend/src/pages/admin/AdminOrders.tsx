import { useState } from 'react';
import { Search, Eye, Filter } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useToast } from '../../hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';

interface Order {
  id: string;
  orderNumber: string;
  customer: string;
  email: string;
  items: number;
  total: number;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  date: string;
  paymentMethod: string;
}

export const AdminOrders = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const [orders, setOrders] = useState<Order[]>([
    { id: '1', orderNumber: 'ORD-2024-0001', customer: 'Rajesh Kumar', email: 'rajesh@example.com', items: 2, total: 166980, status: 'delivered', date: '2024-01-15', paymentMethod: 'Razorpay' },
    { id: '2', orderNumber: 'ORD-2024-0002', customer: 'Priya Sharma', email: 'priya@example.com', items: 1, total: 99990, status: 'shipped', date: '2024-01-16', paymentMethod: 'PhonePe' },
    { id: '3', orderNumber: 'ORD-2024-0003', customer: 'Amit Patel', email: 'amit@example.com', items: 3, total: 175470, status: 'processing', date: '2024-01-17', paymentMethod: 'Paytm' },
    { id: '4', orderNumber: 'ORD-2024-0004', customer: 'Ananya Singh', email: 'ananya@example.com', items: 1, total: 66990, status: 'pending', date: '2024-01-18', paymentMethod: 'Razorpay' },
    { id: '5', orderNumber: 'ORD-2024-0005', customer: 'Vikram Reddy', email: 'vikram@example.com', items: 2, total: 133580, status: 'cancelled', date: '2024-01-19', paymentMethod: 'UPI' },
  ]);

  const getStatusColor = (status: Order['status']) => {
    switch (status) {
      case 'delivered': return 'bg-green-100 text-green-700';
      case 'shipped': return 'bg-blue-100 text-blue-700';
      case 'processing': return 'bg-purple-100 text-purple-700';
      case 'cancelled': return 'bg-red-100 text-red-700';
      case 'pending': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const updateOrderStatus = (orderId: string, newStatus: Order['status']) => {
    setOrders(orders.map(order => 
      order.id === orderId ? { ...order, status: newStatus } : order
    ));
    toast({ 
      title: 'Order status updated', 
      description: `Order ${orderId} is now ${newStatus}` 
    });
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch =
      order.orderNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8 text-black bg-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-600 mt-1">Manage and track all customer orders</p>
        </div>
        <div className="flex items-center gap-3">
          <Filter className="text-gray-600" size={20} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Orders</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative w-full md:w-1/3">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search by order number or customer..."
          className="pl-10 border-gray-300"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3 px-6 text-left text-sm font-semibold text-gray-700">Order No</th>
                <th className="py-3 px-6 text-left text-sm font-semibold text-gray-700">Customer</th>
                <th className="py-3 px-6 text-left text-sm font-semibold text-gray-700">Items</th>
                <th className="py-3 px-6 text-left text-sm font-semibold text-gray-700">Total</th>
                <th className="py-3 px-6 text-left text-sm font-semibold text-gray-700">Status</th>
                <th className="py-3 px-6 text-left text-sm font-semibold text-gray-700">Date</th>
                <th className="py-3 px-6 text-right text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id} className="border-t hover:bg-gray-50">
                  <td className="py-4 px-6 text-sm font-mono">{order.orderNumber}</td>
                  <td className="py-4 px-6 text-sm">{order.customer}</td>
                  <td className="py-4 px-6 text-sm">{order.items}</td>
                  <td className="py-4 px-6 text-sm font-semibold">₹{order.total.toLocaleString('en-IN')}</td>
                  <td className="py-4 px-6">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm">{order.date}</td>
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <Eye size={16} />
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Order Details Dialog */}
      <Dialog open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
        <DialogContent className="max-w-2xl bg-white text-black">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-gray-900">
              Order Details - {selectedOrder?.orderNumber}
            </DialogTitle>
          </DialogHeader>

          {selectedOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Customer</p>
                  <p className="font-medium">{selectedOrder.customer}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{selectedOrder.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Payment Method</p>
                  <p className="font-medium">{selectedOrder.paymentMethod}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total</p>
                  <p className="font-medium">₹{selectedOrder.total.toLocaleString('en-IN')}</p>
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-500 mb-2">Update Status</p>
                <div className="flex gap-2 flex-wrap">
                  {['pending', 'processing', 'shipped', 'delivered', 'cancelled'].map((status) => (
                    <button
                      key={status}
                      onClick={() => updateOrderStatus(selectedOrder.id, status as Order['status'])}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedOrder.status === status
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

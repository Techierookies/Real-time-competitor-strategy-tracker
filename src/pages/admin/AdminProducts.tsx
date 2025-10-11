import { useState } from 'react';
import { Plus, Search, Upload, Download, AlertTriangle, Edit, Trash2 } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/dialog';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';

interface Product {
  id: string;
  name: string;
  sku: string;
  category: string;
  price: number;
  stock: number;
  status: 'active' | 'inactive';
  image: string;
}

export const AdminProducts = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  const [products] = useState<Product[]>([
    { id: '1', name: 'iPhone 15 Pro Max', sku: 'IP15PM-256', category: 'Smartphones', price: 99990, stock: 45, status: 'active', image: '/placeholder.svg' },
    { id: '2', name: 'iPhone 15 Pro', sku: 'IP15P-128', category: 'Smartphones', price: 83990, stock: 8, status: 'active', image: '/placeholder.svg' },
    { id: '3', name: 'iPhone 15', sku: 'IP15-128', category: 'Smartphones', price: 66990, stock: 2, status: 'active', image: '/placeholder.svg' },
    { id: '4', name: 'iPhone 14', sku: 'IP14-128', category: 'Smartphones', price: 58990, stock: 67, status: 'active', image: '/placeholder.svg' },
    { id: '5', name: 'iphone 16', sku: 'IP16-256', category: 'Smartphones', price: 60990, stock: 0, status: 'inactive', image: '/placeholder.svg' },
  ]);

  const lowStockProducts = products.filter(p => p.stock > 0 && p.stock < 10);
  const outOfStockProducts = products.filter(p => p.stock === 0);

  const handleExport = () => {
    toast({ title: 'Exporting products...', description: 'CSV file will download shortly.' });
  };

  const handleBulkUpload = () => {
    toast({ title: 'Upload CSV', description: 'Bulk upload feature coming soon.' });
  };

  return (
    <div className="space-y-6 bg-white text-black min-h-screen p-6 rounded-xl shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600 mt-1">Manage your product inventory</p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleBulkUpload}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            <Upload size={18} />
            Import CSV
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            <Download size={18} />
            Export
          </button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <Plus size={18} />
                Add Product
              </button>
            </DialogTrigger>

            <DialogContent className="bg-white rounded-xl shadow-lg max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-gray-800">Add New Product</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name" className="text-gray-700 font-medium">Product Name</Label>
                    <Input id="name" placeholder="iPhone 15 Pro Max" className="mt-1 border-gray-300" />
                  </div>
                  <div>
                    <Label htmlFor="sku" className="text-gray-700 font-medium">SKU</Label>
                    <Input id="sku" placeholder="IP15PM-256" className="mt-1 border-gray-300" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="category" className="text-gray-700 font-medium">Category</Label>
                    <Input id="category" placeholder="Smartphones" className="mt-1 border-gray-300" />
                  </div>
                  <div>
                    <Label htmlFor="price" className="text-gray-700 font-medium">Price (₹)</Label>
                    <Input id="price" type="number" placeholder="99990" className="mt-1 border-gray-300" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="stock" className="text-gray-700 font-medium">Stock Quantity</Label>
                    <Input id="stock" type="number" placeholder="50" className="mt-1 border-gray-300" />
                  </div>
                  <div>
                    <Label htmlFor="image" className="text-gray-700 font-medium">Image URL</Label>
                    <Input id="image" placeholder="Upload or paste URL" className="mt-1 border-gray-300" />
                  </div>
                </div>
                <div>
                  <Label htmlFor="description" className="text-gray-700 font-medium">Description</Label>
                  <Textarea id="description" placeholder="Product description..." className="mt-1 border-gray-300" />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                    onClick={() => setIsAddDialogOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    onClick={() => {
                      toast({ title: 'Product added successfully!' });
                      setIsAddDialogOpen(false);
                    }}
                  >
                    Add Product
                  </button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {(lowStockProducts.length > 0 || outOfStockProducts.length > 0) && (
        <div className="grid gap-4 md:grid-cols-2">
          {lowStockProducts.length > 0 && (
            <Card className="border border-orange-400 bg-orange-50 text-orange-700">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <AlertTriangle className="h-4 w-4" /> Low Stock Alert
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{lowStockProducts.length} product(s) running low on stock</p>
              </CardContent>
            </Card>
          )}

          {outOfStockProducts.length > 0 && (
            <Card className="border border-red-400 bg-red-50 text-red-700">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <AlertTriangle className="h-4 w-4" /> Out of Stock
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{outOfStockProducts.length} product(s) out of stock</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <Card className="border border-gray-200 bg-white">
        <CardHeader>
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              placeholder="Search products..."
              className="pl-10 border-gray-300"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.map((product) => (
                <TableRow key={product.id} className="hover:bg-gray-50">
                  <TableCell>{product.name}</TableCell>
                  <TableCell>{product.sku}</TableCell>
                  <TableCell>{product.category}</TableCell>
                  <TableCell>₹{product.price.toLocaleString('en-IN')}</TableCell>
                  <TableCell className={`${product.stock < 10 ? 'text-orange-600 font-medium' : 'text-gray-900'}`}>
                    {product.stock}
                  </TableCell>
                  <TableCell>
                    <Badge variant={product.status === 'active' ? 'default' : 'secondary'}>
                      {product.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon" className="text-blue-600 hover:bg-blue-50">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-red-600 hover:bg-red-50">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

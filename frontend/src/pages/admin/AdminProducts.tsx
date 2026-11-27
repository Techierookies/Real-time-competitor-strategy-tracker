import { useState, useEffect } from "react";
import { Plus, Search, AlertTriangle, Edit, Trash2, Save } from "lucide-react";
import { useToast } from "../../hooks/use-toast";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { Label } from "../../components/ui/label";
import { api } from "../../lib/api";

interface Product {
  id: number;
  name: string;
  sku: string;
  category: string;
  price: number;
  stock: number;
  status: string;
}

export const AdminProducts = () => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editedStock, setEditedStock] = useState<number>(0);

  const [newProduct, setNewProduct] = useState({
    name: "",
    sku: "",
    category: "",
    price: "",
    stock: "",
    status: "active",
  });

  const describe = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback;

  // Fetch the catalogue (the API pages results; 200 covers a store catalogue).
  const fetchProducts = async () => {
    try {
      const data = await api.products(200, 0);
      setProducts(data.products as Product[]);
    } catch (error) {
      toast({ title: "Error loading products", description: describe(error, "Failed to load products.") });
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // Add product (admin only; the API checks the signed-in role).
  const handleAddProduct = async () => {
    if (!newProduct.name || !newProduct.sku || !newProduct.price) {
      toast({ title: "Missing fields", description: "Please fill all required fields." });
      return;
    }
    try {
      await api.createProduct({
        name: newProduct.name,
        sku: newProduct.sku,
        category: newProduct.category || "General",
        price: parseFloat(newProduct.price),
        stock: parseInt(newProduct.stock) || 0,
        status: newProduct.status,
      });
      toast({ title: "Product added" });
      setIsAddDialogOpen(false);
      setNewProduct({ name: "", sku: "", category: "", price: "", stock: "", status: "active" });
      fetchProducts();
    } catch (error) {
      toast({ title: "Could not add product", description: describe(error, "Unable to reach the API.") });
    }
  };

  // Delete product
  const handleDeleteProduct = async (id: number) => {
    if (!confirm("Are you sure you want to delete this product?")) return;
    try {
      await api.deleteProduct(id);
      toast({ title: "Product deleted" });
      fetchProducts();
    } catch (error) {
      toast({ title: "Could not delete product", description: describe(error, "Unable to reach the API.") });
    }
  };

  // Update stock
  const handleUpdateStock = async (id: number) => {
    try {
      await api.updateProduct(id, { stock: editedStock });
      toast({ title: "Stock updated" });
      setEditingId(null);
      fetchProducts();
    } catch (error) {
      toast({ title: "Could not update stock", description: describe(error, "Unable to reach the API.") });
    }
  };

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const lowStockProducts = filteredProducts.filter((p) => p.stock > 0 && p.stock < 10);
  const outOfStockProducts = filteredProducts.filter((p) => p.stock === 0);

  return (
    <div className="space-y-6 bg-white text-black min-h-screen p-6 rounded-xl shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Store Products</h1>
          <p className="text-gray-600 mt-1">Manage store inventory dynamically</p>
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Plus size={18} />
              Add Product
            </button>
          </DialogTrigger>

          <DialogContent className="bg-white rounded-xl shadow-lg max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold text-gray-800">
                Add New Product
              </DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Product Name</Label>
                  <Input
                    id="name"
                    value={newProduct.name}
                    onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                    placeholder="iPhone 17 Pro"
                  />
                </div>
                <div>
                  <Label htmlFor="sku">SKU</Label>
                  <Input
                    id="sku"
                    value={newProduct.sku}
                    onChange={(e) => setNewProduct({ ...newProduct, sku: e.target.value })}
                    placeholder="IP17PRO-128"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={newProduct.category}
                    onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
                    placeholder="Smartphones"
                  />
                </div>
                <div>
                  <Label htmlFor="price">Price (₹)</Label>
                  <Input
                    id="price"
                    type="number"
                    value={newProduct.price}
                    onChange={(e) => setNewProduct({ ...newProduct, price: e.target.value })}
                    placeholder="99999"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="stock">Stock</Label>
                  <Input
                    id="stock"
                    type="number"
                    value={newProduct.stock}
                    onChange={(e) => setNewProduct({ ...newProduct, stock: e.target.value })}
                    placeholder="10"
                  />
                </div>
                <div>
                  <Label htmlFor="status">Status</Label>
                  <select
                    id="status"
                    value={newProduct.status}
                    onChange={(e) => setNewProduct({ ...newProduct, status: e.target.value })}
                    className="w-full mt-1 border border-gray-300 rounded-md p-2"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddProduct}>Add Product</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Alerts */}
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
                <p className="text-sm">{lowStockProducts.length} product(s) running low</p>
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

      {/* Table */}
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
              {filteredProducts.map((p) => (
                <TableRow key={p.id} className="hover:bg-gray-50">
                  <TableCell>{p.name}</TableCell>
                  <TableCell>{p.sku}</TableCell>
                  <TableCell>{p.category}</TableCell>
                  <TableCell>₹{p.price.toLocaleString("en-IN")}</TableCell>
                  <TableCell>
                    {editingId === p.id ? (
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          value={editedStock}
                          onChange={(e) => setEditedStock(Number(e.target.value))}
                          className="w-20"
                        />
                        <Button size="sm" onClick={() => handleUpdateStock(p.id)}>
                          <Save className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <span
                        className={`${
                          p.stock < 10 ? "text-orange-600 font-medium" : "text-gray-900"
                        }`}
                      >
                        {p.stock}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={p.status === "active" ? "default" : "secondary"}>
                      {p.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-blue-600 hover:bg-blue-50"
                        onClick={() => {
                          setEditingId(p.id);
                          setEditedStock(p.stock);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => handleDeleteProduct(p.id)}
                      >
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

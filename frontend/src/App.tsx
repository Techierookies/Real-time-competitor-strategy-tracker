import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AdminLayout } from "./components/Layout/AdminLayout";
import { UserLayout } from "./components/Layout/UserLayout";
import { Home } from "./pages/Home";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";
import { Products } from "./pages/Products";
import { Checkout } from "./pages/Checkout";
import { Privacy } from "./pages/Privacy";
import { Cart } from "./pages/Cart";
import { Terms } from "./pages/Terms";
import { Support } from "./pages/Support";
import { AdminDashboard } from "./pages/admin/AdminDashboard";
import { AdminOrders } from "./pages/admin/AdminOrders";
import { AdminProducts } from "./pages/admin/AdminProducts";
import { AdminSettings } from "./pages/admin/AdminSettings";
import { AdminUsers } from "./pages/admin/AdminUsers";
import { AdminReviews } from "./pages/admin/AdminReviews";

function App() {
  return (
    <AuthProvider>
      <Routes>
      <Route path="/" element={<UserLayout />}>
      <Route index element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="checkout" element={<Checkout />} />
        <Route path="products" element={<Products />} />
        <Route path="cart" element={<Cart />} />
        <Route path="support" element={<Support />} />
        <Route path="privacy" element={<Privacy />} />
        <Route path="terms" element={<Terms />} />
        </Route>

        <Route path="/admin" element={
              <ProtectedRoute requireAdmin>
                <AdminLayout />
              </ProtectedRoute>}>/
              <Route index element={<AdminDashboard />} />
              <Route path="orders" element={<AdminOrders />} />
              <Route path="products" element={<AdminProducts />} />
              <Route path="settings" element={<AdminSettings />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="reviews" element={<AdminReviews />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
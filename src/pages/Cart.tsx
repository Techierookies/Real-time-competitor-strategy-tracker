import { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Minus, Plus, Trash2, ShoppingBag, Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface CartItem {
  id: string;
  name: string;
  price: number;
  image: string;
  color: string;
  storage: string;
  quantity: number;
}

const formatPrice = (price: number) => {
  return price.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  });
};


export const Cart = () => {
  const navigate = useNavigate();
  const [cartItems, setCartItems] = useState<CartItem[]>([
    {
      id: '1',
      name: 'iPhone 15 Pro Max',
      price: 1199,
      image: '/iphones/iphone-15.jpeg',
      color: 'Natural Titanium',
      storage: '256GB',
      quantity: 1,
    },
    {
      id: '2',
      name: 'iPhone 15 Pro',
      price: 999,
      image: '/iphones/Iphone-16.jpeg',
      color: 'Blue Titanium',
      storage: '128GB',
      quantity: 2,
    },
  ]);

  const updateQuantity = (id: string, newQuantity: number) => {
    if (newQuantity === 0) {
      removeItem(id);
      return;
    }
    setCartItems(items =>
      items.map(item =>
        item.id === id ? { ...item, quantity: newQuantity } : item
      )
    );
  };

  const removeItem = (id: string) => {
    setCartItems(items => items.filter(item => item.id !== id));
  };

  const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const shipping = 0; // Free shipping
  const tax = Math.round(subtotal * 0.08 * 100) / 100;
  const total = subtotal + shipping + tax;

  const handleCheckout = () => {
    navigate('/checkout', { state: { cartItems } });
  };

  if (cartItems.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16">
        <Card className="max-w-md mx-auto p-8 text-center">
          <ShoppingBag className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-foreground mb-2">Your cart is empty</h2>
          <p className="text-muted-foreground mb-6">
            Start shopping to add items to your cart
          </p>
          <Button onClick={() => navigate('/products')}>
            Continue Shopping
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-foreground">Shopping Cart</h1>
        <Badge variant="secondary">{cartItems.length} items</Badge>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {cartItems.map((item) => (
            <Card key={item.id} className="p-4 shadow-lg rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm">
              <div className="flex gap-4">
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-26 h-26 object-cover rounded-lg"
                />

                <div className="flex-1">
                  <h3 className="font-semibold text-foreground">{item.name}</h3>
                  <p className="text-sm text-muted-foreground mb-2">{item.storage}</p>

                  {/* Color Swatches */}
                  <div className="flex gap-2 items-center mb-2">
                    <span className="text-xs text-muted-foreground">Color:</span>
                    <div className="flex gap-2">
                      <div
                        className={`w-5 h-5 rounded-full border cursor-pointer ${
                          item.color === "Natural Titanium" ? "ring-2 ring-offset-1 ring-gray-400" : ""
                        }`}
                        style={{ backgroundColor: "#d1d5db" }}
                      ></div>
                      <div
                        className={`w-5 h-5 rounded-full border cursor-pointer ${
                          item.color === "Blue Titanium" ? "ring-2 ring-offset-1 ring-blue-400" : ""
                        }`}
                        style={{ backgroundColor: "#1e40af" }}
                      ></div>
                      <div
                        className={`w-5 h-5 rounded-full border cursor-pointer ${
                          item.color === "White Titanium" ? "ring-2 ring-offset-1 ring-gray-200" : ""
                        }`}
                        style={{ backgroundColor: "#f3f4f6" }}
                      ></div>
                      <div
                        className={`w-5 h-5 rounded-full border cursor-pointer ${
                          item.color === "Black Titanium" ? "ring-2 ring-offset-1 ring-black" : ""
                        }`}
                        style={{ backgroundColor: "#0a0a0a" }}
                      ></div>
                    </div>
                  </div>

                  <p className="text-lg font-semibold text-foreground">{formatPrice(item.price)}</p>
                </div>

                <div className="flex flex-col items-end justify-between">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeItem(item.id)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      disabled={item.quantity <= 1}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="w-8 text-center font-medium">{item.quantity}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}

          {/* Continue Shopping */}
          <Card className="p-4 shadow-lg rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm">
            <Button variant="outline" onClick={() => navigate('/products')}>
              <Heart className="h-4 w-4 mr-2" />
              Continue Shopping
            </Button>
          </Card>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <Card className="p-6 shadow-lg rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-sm sticky top-6">
            <h2 className="text-xl font-semibold mb-4 text-foreground">Order Summary</h2>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="text-foreground">${subtotal}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Shipping</span>
                <span className="text-foreground">
                  {shipping === 0 ? (
                    <Badge variant="secondary" className="text-xs">Free</Badge>
                  ) : (
                    `$${shipping}`
                  )}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tax</span>
                <span className="text-foreground">${tax}</span>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="flex justify-between text-lg font-semibold mb-6">
              <span className="text-foreground">Total</span>
              <span className="text-foreground">${total}</span>
            </div>

            <Button className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 text-white" onClick={handleCheckout}>
              Proceed to Checkout
            </Button>

            <p className="text-xs text-muted-foreground text-center mt-4">
              Free shipping on orders over $99
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
};

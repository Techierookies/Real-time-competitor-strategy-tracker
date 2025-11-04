import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { mockiPhones } from '../data/mockData';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card } from '../components/ui/card';
import { Star, Minus, Plus, ShoppingCart, Zap } from 'lucide-react';

export const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedColor, setSelectedColor] = useState(0);
  const [selectedStorage, setSelectedStorage] = useState(0);
  const [quantity, setQuantity] = useState(1);

  const product = mockiPhones.find((p) => p.id === id);

  if (!product) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-semibold text-gray-800">Product not found</h1>
        <Button onClick={() => navigate('/products')} className="mt-4">
          Back to Products
        </Button>
      </div>
    );
  }

  const handleAddToCart = () => {
    console.log('Added to cart:', { product, selectedColor, selectedStorage, quantity });
  };

  const formatPrice = (price: number) =>
    price.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });

  const handleBuyNow = () => {
    navigate('/checkout', {
      state: {
        product,
        selectedColor: product.colors[selectedColor],
        selectedStorage: product.storage[selectedStorage],
        quantity,
      },
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-pink-50 py-10">
      <div className="container mx-auto px-6 max-w-6xl">
        {/* Breadcrumb */}
        <nav className="mb-8 text-sm text-gray-500">
          <span onClick={() => navigate('/')} className="cursor-pointer hover:text-indigo-600">
            Home
          </span>
          <span className="mx-2">/</span>
          <span onClick={() => navigate('/products')} className="cursor-pointer hover:text-indigo-600">
            Products
          </span>
          <span className="mx-2">/</span>
          <span className="text-gray-900 font-medium">{product.name}</span>
        </nav>

        <div className="grid lg:grid-cols-2 gap-14 items-start">
          {/* Product Image */}
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-200 to-pink-200 rounded-3xl blur-3xl opacity-30 group-hover:opacity-50 transition"></div>
            <div className="glass rounded-2xl p-8 bg-gradient-to-br from-background to-muted/20">
              <img
                src={product.image}
                alt={product.name}
                className="w-full max-w-md mx-auto rounded-2xl hover:scale-105 transition-transform duration-500"
              />
            </div>

            {product.isNew && (
              <Badge className="absolute top-4 left-4 bg-gradient-to-r from-indigo-600 to-pink-600 text-white px-4 py-1 rounded-full">
                New Release
              </Badge>
            )}
          </div>

          {/* Product Info */}
          <div className="space-y-6">
            <div>
              <h1 className="text-4xl font-extrabold text-gray-900 mb-3">{product.name}</h1>
              <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`h-5 w-5 ${
                        i < Math.floor(product.rating)
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <span className="text-sm text-gray-600">
                  {product.rating} ({product.reviews} reviews)
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed max-w-lg">{product.description}</p>
            </div>

            {/* Price */}
            <div className="flex items-end gap-3">
              <span className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-pink-600 bg-clip-text text-transparent">
                {formatPrice(product.price)}
              </span>
              {product.originalPrice && (
                <span className="text-xl text-gray-400 line-through">
                  {formatPrice(product.originalPrice)}
                </span>
              )}
            </div>

            {/* Color Selection */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">Choose your color</h3>
              <div className="flex flex-wrap gap-3">
                {product.colors.map((color, index) => (
                  <button
                    key={color}
                    onClick={() => setSelectedColor(index)}
                    className={`px-5 py-2 rounded-xl border text-sm transition-all ${
                      selectedColor === index
                        ? 'border-pink-500 bg-pink-100 text-pink-700 font-medium'
                        : 'border-gray-300 hover:border-pink-400 hover:bg-pink-50'
                    }`}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>

            {/* Storage Selection */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">Storage</h3>
              <div className="flex flex-wrap gap-3">
                {product.storage.map((storage, index) => (
                  <button
                    key={storage}
                    onClick={() => setSelectedStorage(index)}
                    className={`px-5 py-2 rounded-xl border text-sm transition-all ${
                      selectedStorage === index
                        ? 'border-indigo-500 bg-indigo-100 text-indigo-700 font-medium'
                        : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50'
                    }`}
                  >
                    {storage}
                  </button>
                ))}
              </div>
            </div>

            {/* Quantity */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">Quantity</h3>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  disabled={quantity <= 1}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-12 text-center font-medium">{quantity}</span>
                <Button variant="outline" size="icon" onClick={() => setQuantity(quantity + 1)}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Features */}
            <Card className="p-5 bg-white/70 backdrop-blur-xl border border-white/20 shadow-lg">
              <h3 className="font-semibold text-gray-900 mb-3">Key Features</h3>
              <ul className="space-y-2">
                {product.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-gray-700 text-sm">
                    <div className="w-2 h-2 bg-gradient-to-r from-indigo-500 to-pink-500 rounded-full"></div>
                    {feature}
                  </li>
                ))}
              </ul>
            </Card>

            {/* Buttons */}
            <div className="flex gap-4 mt-8">
              <Button
                variant="outline"
                className="flex-1 border-gray-300 hover:border-pink-500 hover:bg-pink-50"
                onClick={handleAddToCart}
              >
                <ShoppingCart className="h-4 w-4 mr-2 text-pink-600" />
                Add to Cart
              </Button>
              <Button
                className="flex-1 bg-gradient-to-r from-indigo-600 to-pink-600 text-white font-medium hover:scale-105 transition"
                onClick={handleBuyNow}
              >
                <Zap className="h-4 w-4 mr-2" />
                Buy Now
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

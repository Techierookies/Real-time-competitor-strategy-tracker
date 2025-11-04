import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Grid, List, Star, Eye } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { mockiPhones } from '../data/mockData';
import { cn } from '../lib/utils';

export const Products = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('name');

  const formatPrice = (price: number) => {
    return price.toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    });
  };
  

  const sortedPhones = useMemo(() => {
    return [...mockiPhones].sort((a, b) => {
      switch (sortBy) {
        case 'price-low':
          return a.price - b.price;
        case 'price-high':
          return b.price - a.price;
        case 'rating':
          return b.rating - a.rating;
        default:
          return a.name.localeCompare(b.name);
      }
    });
  }, [sortBy]);

  return (
    <div className="container mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6 text-center md:text-left">
        <h1 className="font-display text-4xl md:text-5xl text-center font-bold bg-gradient-to-r from-indigo-600 via-pink-500 to-red-500 bg-clip-text text-transparent">
          iPhone Collection
        </h1>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-6">
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-gray-500">
            {sortedPhones.length} products
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md bg-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 shadow-sm"
          >
            <option value="name">Sort by Name</option>
            <option value="price-low">Price: Low to High</option>
            <option value="price-high">Price: High to Low</option>
            <option value="rating">Highest Rated</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'ghost'}
            size="icon"
            className="bg-blue-500 text-white hover:bg-blue-600 p-2 rounded-md"
            onClick={() => setViewMode('grid')}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'ghost'}
            size="icon"
            className="bg-blue-500 text-white hover:bg-blue-600 p-2 rounded-md"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Products Grid/List */}
      <div
        className={cn(
          viewMode === 'grid'
            ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6'
            : 'space-y-4'
        )}
      >
        {sortedPhones.map((phone) => (
          <Card
            key={phone.id}
            className={cn(
              "bg-white border border-gray-200 rounded-3xl shadow-md hover:shadow-xl transition-transform duration-300 overflow-hidden",
              viewMode === 'list' && 'flex flex-row items-center'
            )}
          >
            <CardContent
              className={cn(
                "p-4",
                viewMode === 'list' && 'flex items-center space-x-5'
              )}
            >
              {/* Image */}
              <div
                className={cn(
                  "bg-white-50 rounded-2xl flex items-center justify-center overflow-hidden shadow-sm",
                  viewMode === 'grid'
                    ? 'aspect-square w-full h-48 mb-4 hover:scale-105 transition-transform duration-300'
                    : 'w-32 h-32 flex-shrink-0 hover:scale-105 transition-transform duration-300'
                )}
              >
                <img
                  src={phone.image}
                  alt={phone.name}
                  className="w-full h-full object-contain"
                />
              </div>

              {/* Content */}
              <div className="flex-1 flex flex-col justify-between space-y-3">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-display text-lg md:text-xl font-semibold text-gray-900">
                      {phone.name}
                    </h3>
                    {phone.isNew && (
                      <span className="inline-block mt-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                        New
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-lg md:text-xl font-bold text-gray-900">
                      {formatPrice(phone.price)}
                    </div>
                    {phone.originalPrice && (
                      <div className="text-xs text-gray-400 line-through">
                        {formatPrice(phone.originalPrice)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Rating */}
                <div className="flex items-center space-x-1">
                  <div className="flex items-center">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span className="ml-1 text-xs font-medium text-gray-700">
                      {phone.rating}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    ({phone.reviews} reviews)
                  </span>
                </div>

                {/* Description */}
                <p className="text-gray-600 text-xs md:text-sm line-clamp-2">
                  {phone.description}
                </p>

                {/* Colors */}
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">Colors:</span>
                  <div className="flex space-x-1">
                    {phone.colors.slice(0, 4).map((color, index) => {
                      const colorClass = {
                        Red: 'bg-red-500',
                        Blue: 'bg-blue-500',
                        Green: 'bg-green-500',
                        Black: 'bg-black',
                        White: 'bg-white border',
                        Gold: 'bg-yellow-400',
                        Silver: 'bg-gray-300',
                      }[color] || 'bg-gray-400';

                      return (
                        <div
                          key={index}
                          className={cn(
                            `w-4 h-4 rounded-full border border-gray-200 ${colorClass} hover:scale-110 transition-transform cursor-pointer`
                          )}
                          title={color}
                        />
                      );
                    })}
                    {phone.colors.length > 4 && (
                      <span className="text-xs text-gray-500">
                        +{phone.colors.length - 4}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div
                  className={cn(
                    "flex gap-2 mt-3",
                    viewMode === 'list' ? 'flex-row' : 'flex-col'
                  )}
                >
                  <Button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-1 rounded-lg">
                    Add to Cart
                  </Button>
                  <Button
                    variant="glass"
                    className={cn(
                      viewMode === 'list' ? 'flex-shrink-0' : 'flex-1 text-sm py-1 rounded-lg'
                    )}
                    onClick={() => navigate(`/products/${phone.id}`)}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    Quick View
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

import { Link } from 'react-router-dom';
import { ArrowRight, Star, ShoppingCart } from 'lucide-react';
import heroImage from '../assets/iphone-15-pro-max-hero.jpg';
import colorsImage from '../assets/iphone-15-pro-colors.jpg';
import { mockiPhones } from '../data/mockData';


export const Home = () => {
  const featuredPhones = mockiPhones.filter(phone => phone.isFeatured).slice(0, 3);

  const formatPrice = (price: number) => {
    return price.toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    });
  };
  

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-pink-100">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-100 via-white to-pink-100 py-10 md:py-16">
        <div className="container mx-auto px-16">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* Left content */}
            <div className="space-y-6 text-center md:text-left">
              <div className="inline-flex items-center px-4 py-2 bg-white/60 backdrop-blur-md text-indigo-700 rounded-full text-sm font-medium shadow">
                <span className="mr-2">✨</span>
                New iPhone 17 Pro 
              </div>

              <h1 className="font-display text-5xl md:text-7xl font-extrabold text-gray-900 leading-tight tracking-tight">
                Titanium build.
                <br />
                <span className="bg-gradient-to-r from-indigo-600 to-pink-600 bg-clip-text text-transparent px-10">
                  So strong.
                </span>
                <br />
                <span> Incredibly light.</span>
                
              </h1>

              <p className="text-lg text-gray-700 max-w-md mx-auto md:mx-0 leading-relaxed">
                Forged in titanium and featuring the groundbreaking A17 Pro chip, 
                iPhone 17 Pro brings you the ultimate iPhone experience.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                <Link to="/products">
                  <button className="bg-gradient-to-r from-indigo-600 to-pink-600 text-white px-8 py-3 rounded-full text-lg font-semibold shadow-lg hover:scale-105 transition flex items-center gap-2">
                    Shop iPhone
                    <ArrowRight className="h-5 w-5" />
                  </button>
                </Link>

                <button className="border border-indigo-200 text-indigo-700 px-8 py-3 rounded-full text-lg font-medium hover:bg-white/50 backdrop-blur-sm transition shadow-sm">
                  Learn more
                </button>
              </div>

              <div className="flex flex-wrap justify-center md:justify-start gap-8 text-sm text-gray-600 pt-4">
                <div className="flex items-center">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400 mr-1" />
                  <span>4.8 rating</span>
                </div>
                <div>Free delivery</div>
                <div>90-day returns</div>
              </div>
            </div>

            {/* Right image */}
            <div className="relative flex justify-center">
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-200 to-pink-200 rounded-3xl blur-3xl opacity-40"></div>
              <img 
                src={heroImage} 
                alt="iPhone 15 Pro Max" 
                className="relative z-10 w-full max-w-lg mx-auto rounded-2xl shadow-2xl hover:scale-105 transition"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-20">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Featured iPhones
            </h2>
            <p className="text-gray-700 max-w-2xl mx-auto">
              Discover our most popular iPhone models with cutting-edge features and premium design.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {featuredPhones.map((phone) => (
              <div 
                key={phone.id} 
                className="backdrop-blur-xl bg-white/70 rounded-2xl shadow-xl hover:shadow-2xl transition transform hover:-translate-y-1 px-6 py-6"
              >
                <div className="flex flex-col">
                  <div className="w-full h-56 bg-gray-50 rounded-lg flex items-center justify-center overflow-hidden shadow-inner">
                    <img 
                      src={phone.image} 
                      alt={phone.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  
                  <div className="space-y-3 mt-4">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {phone.name}
                    </h3>

                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-2xl font-bold text-indigo-600">
                          {formatPrice(phone.price)}
                        </span>
                        {phone.originalPrice && (
                          <span className="text-sm text-gray-400 line-through ml-2">
                            {formatPrice(phone.originalPrice)}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center text-sm text-gray-500">
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400 mr-1" />
                        {phone.rating}
                      </div>
                    </div>

                    <p className="text-gray-600 text-sm line-clamp-2">
                      {phone.description}
                    </p>

                    <Link to={`/products/${phone.id}`} className="block">
                      <button className="w-full bg-blue-500 hover:bg-blue-60 text-white py-2 px-4 rounded-xl font-medium hover:scale-105 transition flex items-center justify-center gap-2">
                        <ShoppingCart className="h-4 w-4" />
                        Quick View
                      </button>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trade-in Section */}
      <section className="py-16">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <img 
                src={colorsImage} 
                alt="iPhone 15 Pro Colors" 
                className="w-full rounded-3xl shadow-xl hover:scale-105 transition"
              />
            </div>
            
            <div className="space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
                Trade in for credit.
                <br />
                <span className="bg-gradient-to-r from-indigo-600 to-pink-600 bg-clip-text text-transparent">
                  Save even more.
                </span>
              </h2>

              <p className="text-lg text-gray-700">
                Get credit toward your new iPhone when you trade in your current device. 
                It's good for you and the planet.
              </p>

              <ul className="space-y-3 text-gray-700">
                <li className="flex items-center gap-3">
                  <span className="w-2 h-2 bg-indigo-600 rounded-full"></span>
                  Up to $800 trade-in value
                </li>
                <li className="flex items-center gap-3">
                  <span className="w-2 h-2 bg-indigo-600 rounded-full"></span>
                  Free iPhone setup and data transfer
                </li>
                <li className="flex items-center gap-3">
                  <span className="w-2 h-2 bg-indigo-600 rounded-full"></span>
                  Environmentally responsible recycling
                </li>
              </ul>

              <button className="bg-gradient-to-r from-indigo-600 to-pink-600 text-white px-6 py-3 rounded-xl font-medium shadow hover:scale-105 transition">
                Get your trade-in estimate
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* AI Recommendation Placeholder */}
      <section className="py-16">
        <div className="container mx-auto px-6">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Recommended for You
            </h2>
            <p className="text-gray-700 mb-12">
              AI-powered recommendations based on your preferences and browsing history.
            </p>

            <div className="backdrop-blur-xl bg-white/70 shadow-2xl rounded-2xl p-12 max-w-2xl mx-auto">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto shadow-inner">
                  <Star className="h-8 w-8 text-indigo-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  AI Recommendations Coming Soon
                </h3>
                <p className="text-gray-600">
                  Our AI engine is learning your preferences to provide personalized iPhone recommendations.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

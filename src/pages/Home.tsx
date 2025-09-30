import { Link } from 'react-router-dom';
import { ArrowRight, Star, ShoppingCart } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { mockiPhones } from '../data/mockData';
import heroImage from '../assets/iphone-15-pro-max-hero.jpg';
import colorsImage from '../assets/iphone-15-pro-colors.jpg';

export const Home = () => {
  const featuredPhones = mockiPhones.filter(phone => phone.isFeatured).slice(0, 3);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-secondary to-background overflow-hidden">
        <div className="container mx-auto px-4 py-16 md:py-24">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center px-4 py-2 bg-accent/10 text-accent rounded-full text-sm font-medium">
                <span className="mr-2">✨</span>
                New iPhone 15 Pro Max
              </div>
              
              <h1 className="font-display text-4xl md:text-6xl font-bold text-primary leading-tight">
                Titanium.
                <br />
                <span className="text-accent">So strong.</span>
                <br />
                So light.
              </h1>
              
              <p className="text-lg text-foreground/70 max-w-md">
                Forged in titanium and featuring the groundbreaking A17 Pro chip, 
                iPhone 15 Pro Max brings you the ultimate iPhone experience.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/products">
                  <Button variant="hero" size="lg" className="group">
                    Shop iPhone
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                
                <Button variant="glass" size="lg">
                  Learn more
                </Button>
              </div>
              
              <div className="flex items-center space-x-6 text-sm text-foreground/60">
                <div className="flex items-center">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400 mr-1" />
                  <span>4.8 rating</span>
                </div>
                <div>Free delivery</div>
                <div>90-day returns</div>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-accent/20 to-primary/20 rounded-3xl blur-3xl transform rotate-3"></div>
              <img 
                src={heroImage} 
                alt="iPhone 15 Pro Max" 
                className="relative z-10 w-full max-w-lg mx-auto hover-lift"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products Carousel */}
      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl md:text-4xl font-bold text-primary mb-4">
              Featured iPhones
            </h2>
            <p className="text-foreground/70 max-w-2xl mx-auto">
              Discover our most popular iPhone models with cutting-edge features and premium design.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {featuredPhones.map((phone) => (
              <Card key={phone.id} className="hover-lift card-premium border-0">
                <CardContent className="p-6">
                  <div className="aspect-square bg-secondary/50 rounded-2xl mb-6 flex items-center justify-center">
                    <img 
                      src={phone.image} 
                      alt={phone.name}
                      className="w-32 h-32 object-contain"
                    />
                  </div>
                  
                  <div className="space-y-3">
                    <h3 className="font-display text-xl font-semibold text-primary">
                      {phone.name}
                    </h3>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-2xl font-bold text-primary">
                          ${phone.price}
                        </span>
                        {phone.originalPrice && (
                          <span className="text-sm text-foreground/50 line-through ml-2">
                            ${phone.originalPrice}
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center text-sm text-foreground/70">
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400 mr-1" />
                        {phone.rating}
                      </div>
                    </div>
                    
                    <p className="text-foreground/70 text-sm line-clamp-2">
                      {phone.description}
                    </p>
                    
                    <Link to={`/products/${phone.id}`} className="block">
                      <Button variant="cta" className="w-full">
                        <ShoppingCart className="h-4 w-4 mr-2" />
                        Quick View
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Trade-in & Offers Section */}
      <section className="py-16 bg-secondary/30">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <img 
                src={colorsImage} 
                alt="iPhone 15 Pro Colors" 
                className="w-full rounded-3xl hover-lift"
              />
            </div>
            
            <div className="space-y-6">
              <h2 className="font-display text-3xl md:text-4xl font-bold text-primary">
                Trade in for credit.
                <br />
                <span className="text-accent">Save even more.</span>
              </h2>
              
              <p className="text-lg text-foreground/70">
                Get credit toward your new iPhone when you trade in your current device. 
                It's good for you and the planet.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-accent rounded-full"></div>
                  <span className="text-foreground/70">Up to $800 trade-in value</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-accent rounded-full"></div>
                  <span className="text-foreground/70">Free iPhone setup and data transfer</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-accent rounded-full"></div>
                  <span className="text-foreground/70">Environmentally responsible recycling</span>
                </div>
              </div>
              
              <Button variant="premium" size="lg">
                Get your trade-in estimate
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* AI Recommendations Placeholder */}
      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <h2 className="font-display text-3xl md:text-4xl font-bold text-primary mb-4">
              Recommended for You
            </h2>
            <p className="text-foreground/70 mb-12">
              AI-powered recommendations based on your preferences and browsing history.
            </p>
            
            <div className="glass rounded-3xl p-12 max-w-2xl mx-auto">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-accent/20 rounded-full flex items-center justify-center mx-auto">
                  <Star className="h-8 w-8 text-accent" />
                </div>
                <h3 className="font-display text-xl font-semibold text-primary">
                  AI Recommendations Coming Soon
                </h3>
                <p className="text-foreground/70">
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
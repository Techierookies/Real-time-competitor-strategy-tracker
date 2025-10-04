export interface iPhone {
    id: string;
    name: string;
    model: string;
    price: number;
    originalPrice?: number;
    image: string;
    rating: number;
    reviews: number;
    colors: string[];
    storage: string[];
    description: string;
    features: string[];
    isNew?: boolean;
    isFeatured?: boolean;
  }
  
  export interface Review {
    id: string;
    userId: string;
    userName: string;
    rating: number;
    comment: string;
    date: string;
  }
  
  export interface CompetitorData {
    id: string;
    competitor: string;
    model: string;
    price: number;
    change: number;
    lastUpdated: string;
  }
  
  export const mockiPhones: iPhone[] = [
    {
      id: '1',
      name: 'iPhone 15 Pro Max',
      model: 'iPhone 15 Pro Max',
      price: 140900,
      originalPrice: 154900,
      image: '/iphones/iphone-15.jpeg',
      rating: 4.8,
      reviews: 2847,
      colors: ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium'],
      storage: ['256GB', '512GB', '1TB'],
      description: 'The ultimate iPhone experience with the most advanced Pro camera system.',
      features: [
        'A17 Pro chip with 6-core GPU',
        'Pro camera system with 5x Telephoto',
        'Action Button',
        'USB-C connectivity',
        'All-day battery life'
      ],
      isNew: true,
      isFeatured: true,
    },
    {
      id: '2',
      name: 'iPhone 16',
      model: 'iPhone 16',
      price: 74900,
      originalPrice: 79900,
      image: '/iphones/Iphone-16.jpeg',
      rating: 4.7,
      reviews: 1924,
      colors: ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium'],
      storage: ['128GB', '256GB', '512GB', '1TB'],
      description: 'The most advanced iPhone with Pro features in a more compact size.',
      features: [
        'A17 Pro chip',
        'Pro camera system',
        'Action Button',
        'USB-C connectivity',
        'All-day battery life'
      ],
      isNew: true,
      isFeatured: true,
    },
    {
      id: '3',
      name: 'iPhone 17 Pro',
      model: 'iPhone 17 Pro',
      price: 134900,
      originalPrice: 140600,
      image: '/iphones/Iphone-17.jpeg',
      rating: 4.6,
      reviews: 3421,
      colors: ['Pink', 'Yellow', 'Green', 'Blue', 'Black'],
      storage: ['128GB', '256GB', '512GB', '1TB'],
      description: 'A total powerhouse with an all-new 48MP Main camera.',
      features: [
        'A18 Bionic chip',
        '48MP Main + Ultra Wide camera',
        'USB-C connectivity',
        'All-day battery life',
        'Ceramic Shield'
      ],
      isFeatured: true,
      isNew: true,
    },
    {
      id: '4',
      name: 'iPhone 15',
      model: 'iPhone 15',
      price: 57999,
      originalPrice: 60900,
      image: '/iphones/iphone-15pink.jpg',
      rating: 4.5,
      reviews: 5632,
      colors: ['Blue', 'Purple', 'Yellow', 'Midnight', 'Starlight', 'Red'],
      storage: ['128GB', '256GB', '512GB'],
      description: 'The iPhone that brings you incredible camera capabilities.',
      features: [
        'A15 Bionic chip',
        'Advanced dual-camera system',
        'Crash Detection',
        'All-day battery life',
        'Ceramic Shield'
      ],
    },
    {
      id: '5',
      name: 'iPhone 16 pro',
      model: 'iPhone 16 pro',
      price: 121900,
      originalPrice: 129900,
      image: '/iphones/iphone-16pro.jpg',
      rating: 4.4,
      reviews: 7421,
      colors: ['Pink', 'Blue', 'Midnight', 'Starlight', 'Red'],
      storage: ['128GB', '256GB', '512GB'],
      description: 'Powerful performance with the A15 Bionic chip and stunning OLED display.',
      features: [
        'A15 Bionic chip',
        'Dual-camera system',
        'Super Retina XDR display',
        'All-day battery life',
        '5G connectivity'
      ],
    },
    {
      id: '6',
      name: 'iPhone 16 pro max',
      model: 'iPhone 16 pro max',
      price: 114999,
      originalPrice: 124990,
      image: '/iphones/iphone-16promax.jpeg',
      rating: 4.3,
      reviews: 8123,
      colors: ['Blue', 'Green', 'Red', 'White', 'Black', 'Purple'],
      storage: ['64GB', '128GB', '256GB'],
      description: 'A sleek design with OLED display and powerful A14 Bionic chip.',
      features: [
        'A14 Bionic chip',
        'Dual 12MP camera system',
        'Ceramic Shield',
        'Super Retina XDR display',
        '5G connectivity'
      ],
    }
  ];
  
  export const mockReviews: Review[] = [
    {
      id: '1',
      userId: '1',
      userName: 'Sarah M.',
      rating: 5,
      comment: 'Amazing camera quality and the titanium build feels incredibly premium. Best iPhone yet!',
      date: '2024-01-15',
    },
    {
      id: '2',
      userId: '2',
      userName: 'Mike R.',
      rating: 4,
      comment: 'Great performance and battery life. The Action Button is a nice touch.',
      date: '2024-01-12',
    },
    {
      id: '3',
      userId: '3',
      userName: 'Emily K.',
      rating: 5,
      comment: 'Love the new colors and the camera improvements are noticeable.',
      date: '2024-01-10',
    },
  ];
  
  export const mockCompetitorData: CompetitorData[] = [
    {
      id: '1',
      competitor: 'Samsung',
      model: 'Galaxy S24 Ultra',
      price: 1199,
      change: -2.5,
      lastUpdated: '2024-01-15 10:30',
    },
    {
      id: '2',
      competitor: 'Google',
      model: 'Pixel 8 Pro',
      price: 999,
      change: 1.2,
      lastUpdated: '2024-01-15 09:15',
    },
    {
      id: '3',
      competitor: 'OnePlus',
      model: 'OnePlus 12',
      price: 799,
      change: -1.8,
      lastUpdated: '2024-01-15 08:45',
    },
  ];
  
  export const mockNotifications = [
    {
      id: '1',
      type: 'price_alert',
      message: 'Samsung Galaxy S24 Ultra price dropped by 2.5%',
      timestamp: '2024-01-15 10:30',
      isRead: false,
    },
    {
      id: '2',
      type: 'competitor_update',
      message: 'Google Pixel 8 Pro received a promotional boost',
      timestamp: '2024-01-15 09:15',
      isRead: false,
    },
    {
      id: '3',
      type: 'sales_milestone',
      message: 'Congratulations! 500 iPhones sold this month',
      timestamp: '2024-01-14 16:20',
      isRead: true,
    },
  ];
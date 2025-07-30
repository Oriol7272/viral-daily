import React, { useEffect, useState } from "react";
import "./App.css";
import axios from "axios";
import { User, Crown, Settings, LogOut, CreditCard } from 'lucide-react';
import SubscriptionPlans from './components/SubscriptionPlans';
import PaymentModal from './components/PaymentModal';
import UserDashboard from './components/UserDashboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PlatformFilter = ({ selectedPlatform, onPlatformChange }) => {
  const platforms = [
    { key: 'all', label: 'All Platforms', color: 'bg-purple-500' },
    { key: 'youtube', label: 'YouTube', color: 'bg-red-500' },
    { key: 'tiktok', label: 'TikTok', color: 'bg-black' },
    { key: 'twitter', label: 'Twitter', color: 'bg-blue-500' }
  ];

  return (
    <div className="flex flex-wrap justify-center gap-3 mb-8">
      {platforms.map(platform => (
        <button
          key={platform.key}
          onClick={() => onPlatformChange(platform.key)}
          className={`px-4 py-2 rounded-full text-white font-medium transition-all duration-200 ${
            selectedPlatform === platform.key 
              ? `${platform.color} scale-105 shadow-lg` 
              : 'bg-gray-400 hover:bg-gray-500'
          }`}
        >
          {platform.label}
        </button>
      ))}
    </div>
  );
};

const VideoCard = ({ video }) => {
  const [imageError, setImageError] = useState(false);
  
  const getPlatformIcon = (platform) => {
    const icons = {
      youtube: '📺',
      tiktok: '🎵',
      twitter: '🐦'
    };
    return icons[platform] || '🎬';
  };

  const getPlatformColor = (platform) => {
    const colors = {
      youtube: 'border-red-500 bg-red-50',
      tiktok: 'border-black bg-gray-50',
      twitter: 'border-blue-500 bg-blue-50',
      instagram: 'border-pink-500 bg-pink-50'
    };
    return colors[platform] || 'border-gray-500 bg-gray-50';
  };

  const getPlatformGradient = (platform) => {
    const gradients = {
      youtube: 'from-red-500 to-red-600',
      tiktok: 'from-black to-gray-800',
      twitter: 'from-blue-500 to-blue-600',
      instagram: 'from-pink-500 to-purple-600'
    };
    return gradients[platform] || 'from-gray-500 to-gray-600';
  };

  const formatViews = (views) => {
    if (!views) return 'N/A';
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toString();
  };

  const getReliableThumbnail = () => {
    if (imageError || !video.thumbnail || video.thumbnail.includes('via.placeholder.com') || video.thumbnail.includes('mock')) {
      // Create inline SVG data URI for reliable thumbnails
      const colors = {
        youtube: '#FF0000',
        tiktok: '#000000', 
        twitter: '#1DA1F2'
      };
      const bgColor = colors[video.platform] || '#6B7280';
      const platformIcons = {
        youtube: '📺',
        tiktok: '🎵',
        twitter: '🐦'
      };
      const icon = platformIcons[video.platform] || '🎬';
      const platformName = video.platform.toUpperCase();
      const score = video.viral_score ? Math.round(video.viral_score) : 'N/A';
      
      // Create clean SVG without special characters
      const svgContent = `<svg width="400" height="225" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="225" fill="${bgColor}"/>
        <rect x="0" y="0" width="400" height="225" fill="url(#grad1)" opacity="0.1"/>
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:white;stop-opacity:0.2" />
            <stop offset="100%" style="stop-color:white;stop-opacity:0" />
          </linearGradient>
        </defs>
        <text x="200" y="90" text-anchor="middle" fill="white" font-size="36" font-weight="bold">${icon}</text>
        <text x="200" y="130" text-anchor="middle" fill="white" font-size="18" font-weight="bold">${platformName}</text>
        <text x="200" y="155" text-anchor="middle" fill="white" font-size="14">Viral Score: ${score}</text>
        <text x="200" y="180" text-anchor="middle" fill="white" font-size="12" opacity="0.8">VIRAL DAILY</text>
      </svg>`;
      
      // Convert to data URI safely
      return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgContent)}`;
    }
    return video.thumbnail;
  };

  return (
    <div className={`bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 hover:scale-105 border-t-4 ${getPlatformColor(video.platform)} animate-fadeInUp`}>
      <div className="relative group">
        <img 
          src={getReliableThumbnail()}
          alt={video.title}
          className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-300"
          onError={() => setImageError(true)}
        />
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300"></div>
        
        {/* Platform Badge */}
        <div className="absolute top-2 right-2 bg-black bg-opacity-80 text-white px-3 py-1 rounded-full text-sm font-medium">
          {getPlatformIcon(video.platform)} {video.platform.toUpperCase()}
        </div>
        
        {/* Viral Score Badge */}
        {video.viral_score && (
          <div className="absolute top-2 left-2 bg-gradient-to-r from-orange-500 to-red-500 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg">
            🔥 {video.viral_score.toFixed(0)}
          </div>
        )}

        {/* Play Button Overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="bg-white bg-opacity-90 rounded-full p-4 shadow-lg">
            <svg className="w-8 h-8 text-gray-800" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      </div>
      
      <div className="p-5">
        <h3 className="font-bold text-lg mb-3 line-clamp-2 hover:text-blue-600 transition-colors cursor-pointer">
          {video.title}
        </h3>
        
        {video.author && (
          <p className="text-gray-600 text-sm mb-3 flex items-center">
            <span className="mr-1">👤</span> {video.author}
          </p>
        )}
        
        <div className="flex justify-between items-center text-sm text-gray-500 mb-4">
          {video.views && (
            <span className="flex items-center bg-gray-100 px-2 py-1 rounded-full">
              <span className="mr-1">👀</span> {formatViews(video.views)}
            </span>
          )}
          {video.likes && (
            <span className="flex items-center bg-red-100 px-2 py-1 rounded-full">
              <span className="mr-1">❤️</span> {formatViews(video.likes)}
            </span>
          )}
        </div>
        
        <a 
          href={video.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className={`block w-full bg-gradient-to-r ${getPlatformGradient(video.platform)} text-white text-center py-3 rounded-lg hover:shadow-lg transition-all duration-200 font-medium`}
        >
          Watch Now 🚀
        </a>
      </div>
    </div>
  );
};

const LoadingCard = () => (
  <div className="bg-white rounded-xl shadow-lg overflow-hidden animate-pulse">
    <div className="h-48 bg-gray-300"></div>
    <div className="p-5">
      <div className="h-4 bg-gray-300 rounded mb-2"></div>
      <div className="h-4 bg-gray-300 rounded w-3/4 mb-3"></div>
      <div className="h-3 bg-gray-300 rounded w-1/2 mb-4"></div>
      <div className="h-10 bg-gray-300 rounded"></div>
    </div>
  </div>
);

const SubscriptionModal = ({ isOpen, onClose, onSubscribe }) => {
  const [email, setEmail] = useState('');
  const [telegram, setTelegram] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [methods, setMethods] = useState([]);

  const handleMethodToggle = (method) => {
    setMethods(prev => 
      prev.includes(method) 
        ? prev.filter(m => m !== method)
        : [...prev, method]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (methods.length === 0) {
      alert('Please select at least one delivery method');
      return;
    }
    
    const subscriptionData = {
      delivery_methods: methods
    };
    
    if (methods.includes('email') && email) subscriptionData.email = email;
    if (methods.includes('telegram') && telegram) subscriptionData.telegram_id = telegram;
    if (methods.includes('whatsapp') && whatsapp) subscriptionData.whatsapp_number = whatsapp;
    
    onSubscribe(subscriptionData);
    setEmail('');
    setTelegram('');
    setWhatsapp('');
    setMethods([]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 modal-backdrop">
      <div className="bg-white rounded-xl p-6 w-full max-w-md transform transition-all duration-300 scale-100">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Get Daily Viral Videos 📱</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Choose delivery methods:</label>
            
            <div className="space-y-2">
              <label className="flex items-center p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={methods.includes('email')}
                  onChange={() => handleMethodToggle('email')}
                  className="mr-3 w-4 h-4"
                />
                📧 Email
              </label>
              
              <label className="flex items-center p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={methods.includes('telegram')}
                  onChange={() => handleMethodToggle('telegram')}
                  className="mr-3 w-4 h-4"
                />
                📱 Telegram
              </label>
              
              <label className="flex items-center p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={methods.includes('whatsapp')}
                  onChange={() => handleMethodToggle('whatsapp')}
                  className="mr-3 w-4 h-4"
                />
                💬 WhatsApp
              </label>
            </div>
          </div>
          
          {methods.includes('email') && (
            <div className="mb-4">
              <input
                type="email"
                placeholder="Your email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>
          )}
          
          {methods.includes('telegram') && (
            <div className="mb-4">
              <input
                type="text"
                placeholder="Your Telegram username (e.g., @username)"
                value={telegram}
                onChange={(e) => setTelegram(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>
          )}
          
          {methods.includes('whatsapp') && (
            <div className="mb-4">
              <input
                type="tel"
                placeholder="Your WhatsApp number (+1234567890)"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all"
            >
              Subscribe 🔔
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

function App() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState('all');
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Monetization states
  const [currentUser, setCurrentUser] = useState(null);
  const [showPricingPage, setShowPricingPage] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showUserDashboard, setShowUserDashboard] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    // Check for stored user data
    const storedUser = localStorage.getItem('viralDailyUser');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setCurrentUser(userData);
        verifyUser(userData);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('viralDailyUser');
      }
    }
    
    fetchVideos(selectedPlatform);
  }, [selectedPlatform]);

  const verifyUser = async (userData) => {
    try {
      const response = await axios.get(`${API}/users/me`, {
        headers: { 'Authorization': `Bearer ${userData.api_key}` }
      });
      
      // Update user data if different
      if (JSON.stringify(response.data) !== JSON.stringify(userData)) {
        setCurrentUser(response.data);
        localStorage.setItem('viralDailyUser', JSON.stringify(response.data));
      }
    } catch (error) {
      console.error('Error verifying user:', error);
      // Clear invalid user data
      setCurrentUser(null);
      localStorage.removeItem('viralDailyUser');
    }
  };

  const registerUser = async (email) => {
    try {
      const response = await axios.post(`${API}/users/register`, { email });
      const userData = response.data;
      
      setCurrentUser(userData);
      localStorage.setItem('viralDailyUser', JSON.stringify(userData));
      
      return userData;
    } catch (error) {
      console.error('Error registering user:', error);
      throw error;
    }
  };

  const fetchVideos = async (platform = null) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Fetching videos from:', API);
      const url = platform && platform !== 'all' 
        ? `${API}/videos?platform=${platform}&limit=20`
        : `${API}/videos?limit=40`;
      
      console.log('API URL:', url);
      
      const headers = {};
      if (currentUser?.api_key) {
        headers['Authorization'] = `Bearer ${currentUser.api_key}`;
      }
      
      const response = await axios.get(url, { headers });
      console.log('API Response:', response.data);
      
      setVideos(response.data.videos || []);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error fetching videos:', err);
      setError('Failed to load viral videos. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (subscriptionData) => {
    try {
      await axios.post(`${API}/subscribe`, subscriptionData);
      alert('Successfully subscribed to daily viral videos! 🎉');
      setShowSubscriptionModal(false);
    } catch (err) {
      console.error('Error subscribing:', err);
      alert('Failed to subscribe. Please try again.');
    }
  };

  const handlePlanSelect = async (plan, cycle) => {
    setBillingCycle(cycle);
    setSelectedPlan(plan);
    
    if (plan.tier === 'free') {
      // Handle free plan signup
      if (!currentUser) {
        const email = prompt('Enter your email to get started:');
        if (email) {
          try {
            await registerUser(email);
            alert('Successfully signed up for the free plan! 🎉');
            setShowPricingPage(false);
          } catch (error) {
            alert('Failed to sign up. Please try again.');
          }
        }
      } else {
        alert('You are already on the free plan!');
      }
    } else {
      // Handle premium plan upgrade
      if (!currentUser) {
        const email = prompt('Enter your email to continue:');
        if (email) {
          try {
            await registerUser(email);
          } catch (error) {
            alert('Failed to create account. Please try again.');
            return;
          }
        } else {
          return;
        }
      }
      
      setShowPaymentModal(true);
      setShowPricingPage(false);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('viralDailyUser');
    setUserMenuOpen(false);
    // Refresh videos to get free tier data
    fetchVideos(selectedPlatform);
  };

  const getTierBadge = (tier) => {
    switch (tier) {
      case 'pro':
        return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'business':
        return <Crown className="w-4 h-4 text-purple-500" />;
      default:
        return null;
    }
  };

  // Auto-refresh every 30 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchVideos(selectedPlatform);
    }, 30 * 60 * 1000);

    return () => clearInterval(interval);
  }, [selectedPlatform, currentUser]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      {/* Pricing Page */}
      {showPricingPage && (
        <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
          <div className="container mx-auto px-4 py-8">
            <div className="text-center mb-8">
              <button
                onClick={() => setShowPricingPage(false)}
                className="absolute top-4 left-4 text-gray-600 hover:text-gray-800"
              >
                ← Back to Videos
              </button>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
                Choose Your Plan
              </h1>
              <p className="text-xl text-gray-600">
                Unlock the full power of viral content discovery
              </p>
            </div>
            
            <SubscriptionPlans 
              onSelectPlan={handlePlanSelect}
              currentUser={currentUser}
            />
          </div>
        </div>
      )}

      {/* Payment Modal */}
      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        selectedPlan={selectedPlan}
        billingCycle={billingCycle}
        user={currentUser}
      />

      {/* User Dashboard */}
      {showUserDashboard && currentUser && (
        <UserDashboard
          user={currentUser}
          onClose={() => setShowUserDashboard(false)}
        />
      )}

      {/* Main App Content */}
      {!showPricingPage && (
        <>
          {/* Header */}
          <header className="bg-white shadow-lg border-b border-gray-100">
            <div className="container mx-auto px-4 py-6">
              <div className="flex flex-col md:flex-row justify-between items-center">
                <div className="text-center md:text-left mb-4 md:mb-0">
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                    🔥 Viral Daily
                  </h1>
                  <p className="text-gray-600 text-lg">
                    Discover the most viral videos from across the web, updated daily!
                  </p>
                  {lastUpdated && (
                    <p className="text-sm text-gray-500 mt-1">
                      Last updated: {lastUpdated}
                    </p>
                  )}
                </div>
                
                <div className="flex items-center gap-3">
                  {/* User Menu */}
                  {currentUser ? (
                    <div className="relative">
                      <button
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                        className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
                      >
                        <User className="w-5 h-5" />
                        <span className="hidden md:inline">
                          {currentUser.name || currentUser.email?.split('@')[0]}
                        </span>
                        {getTierBadge(currentUser.subscription_tier)}
                      </button>
                      
                      {userMenuOpen && (
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-50">
                          <div className="p-2 border-b">
                            <p className="text-sm text-gray-600">{currentUser.email}</p>
                            <p className="text-xs text-gray-500 capitalize">
                              {currentUser.subscription_tier} Plan
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              setShowUserDashboard(true);
                              setUserMenuOpen(false);
                            }}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                          >
                            <Settings className="w-4 h-4" />
                            Dashboard
                          </button>
                          <button
                            onClick={() => {
                              setShowPricingPage(true);
                              setUserMenuOpen(false);
                            }}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                          >
                            <CreditCard className="w-4 h-4" />
                            Upgrade Plan
                          </button>
                          <button
                            onClick={handleLogout}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2 text-red-600"
                          >
                            <LogOut className="w-4 h-4" />
                            Sign Out
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowPricingPage(true)}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-2 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
                    >
                      Sign Up Free
                    </button>
                  )}
                  
                  <button
                    onClick={() => fetchVideos(selectedPlatform)}
                    disabled={loading}
                    className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    {loading ? '🔄 Loading...' : '🔄 Refresh'}
                  </button>
                  
                  <button
                    onClick={() => setShowSubscriptionModal(true)}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-xl hover:from-green-600 hover:to-teal-600 transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    🔔 Get Daily Updates
                  </button>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto px-4 py-8">
            {/* Platform Filter */}
            <PlatformFilter 
              selectedPlatform={selectedPlatform}
              onPlatformChange={setSelectedPlatform}
            />

            {/* Upgrade Banner for Free Users */}
            {currentUser && currentUser.subscription_tier === 'free' && (
              <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold">🚀 Upgrade to Pro for unlimited videos!</h3>
                    <p className="text-sm opacity-90">Remove ads, get unlimited access, and unlock premium features</p>
                  </div>
                  <button
                    onClick={() => setShowPricingPage(true)}
                    className="bg-white text-orange-600 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
                  >
                    Upgrade Now
                  </button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-purple-500 border-t-transparent"></div>
                <p className="mt-4 text-gray-600 text-lg">Loading viral videos...</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-8">
                  {[...Array(8)].map((_, i) => (
                    <LoadingCard key={i} />
                  ))}
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">😵</div>
                <p className="text-red-500 mb-4 text-lg">{error}</p>
                <button
                  onClick={() => fetchVideos(selectedPlatform)}
                  className="px-6 py-3 bg-purple-500 text-white rounded-xl hover:bg-purple-600 transition-all duration-200"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Videos Grid */}
            {!loading && !error && (
              <>
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-gray-800 mb-2">
                    {selectedPlatform === 'all' 
                      ? `🌟 Top ${videos.length} Viral Videos Today` 
                      : `📱 Top ${videos.length} ${selectedPlatform.toUpperCase()} Videos`
                    }
                  </h2>
                  <p className="text-gray-600">Updated every hour with the hottest viral content</p>
                  
                  {/* Plan-specific messaging */}
                  {currentUser && (
                    <p className="text-sm text-purple-600 mt-2">
                      {currentUser.subscription_tier === 'free' 
                        ? `Free plan: Showing videos with ads • Upgrade for unlimited access`
                        : `${currentUser.subscription_tier} plan: Unlimited access • No ads`
                      }
                    </p>
                  )}
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {videos.map((video, index) => (
                    <VideoCard key={video.id || index} video={video} />
                  ))}
                </div>

                {videos.length === 0 && (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">🔍</div>
                    <p className="text-gray-600 text-lg">No viral videos found for the selected platform.</p>
                    <p className="text-gray-500 mt-2">Try selecting a different platform or refreshing the page.</p>
                  </div>
                )}
              </>
            )}
          </main>

          {/* Subscription Modal */}
          <SubscriptionModal
            isOpen={showSubscriptionModal}
            onClose={() => setShowSubscriptionModal(false)}
            onSubscribe={handleSubscribe}
          />

          {/* Footer */}
          <footer className="bg-gradient-to-r from-gray-800 to-gray-900 text-white py-12 mt-16">
            <div className="container mx-auto px-4 text-center">
              <h3 className="text-2xl font-bold mb-2">🔥 Viral Daily</h3>
              <p className="text-gray-300 mb-4">Your daily dose of viral content</p>
              <p className="text-sm text-gray-400 mb-6">
                Aggregating the best viral videos from YouTube, TikTok, Twitter, and Instagram
              </p>
              <div className="flex justify-center space-x-6 mb-6">
                <span className="text-gray-400">📺 YouTube</span>
                <span className="text-gray-400">🎵 TikTok</span>
                <span className="text-gray-400">🐦 Twitter</span>
                <span className="text-gray-400">📷 Instagram</span>
              </div>
              <div className="border-t border-gray-700 pt-6">
                <p className="text-xs text-gray-500">
                  © 2025 Viral Daily. All rights reserved. • 
                  <button
                    onClick={() => setShowPricingPage(true)}
                    className="text-purple-400 hover:text-purple-300 ml-1"
                  >
                    Pricing
                  </button>
                </p>
              </div>
            </div>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;
import React, { useState, useEffect } from 'react';
import { User, Key, BarChart3, CreditCard, Settings, Crown, Zap } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserDashboard = ({ user, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [analytics, setAnalytics] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && activeTab === 'analytics') {
      fetchAnalytics();
    }
    if (user && activeTab === 'billing') {
      fetchTransactions();
    }
  }, [user, activeTab]);

  const fetchAnalytics = async () => {
    if (!user?.api_key) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/users/me/analytics`, {
        headers: { 'Authorization': `Bearer ${user.api_key}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    if (!user?.api_key) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/payments/v1/transactions/me`, {
        headers: { 'Authorization': `Bearer ${user.api_key}` }
      });
      setTransactions(response.data.transactions || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTierIcon = (tier) => {
    switch (tier) {
      case 'pro': return <Crown className="w-5 h-5 text-yellow-500" />;
      case 'business': return <Zap className="w-5 h-5 text-purple-500" />;
      default: return <User className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'pro': return 'from-yellow-400 to-orange-500';
      case 'business': return 'from-purple-500 to-indigo-600';
      default: return 'from-gray-400 to-gray-600';
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const copyApiKey = () => {
    navigator.clipboard.writeText(user.api_key);
    alert('API key copied to clipboard!');
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center mr-4">
                {getTierIcon(user.subscription_tier)}
              </div>
              <div>
                <h2 className="text-2xl font-bold">{user.name || 'User'}</h2>
                <p className="text-purple-100">{user.email}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-4 font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'text-purple-600 border-b-2 border-purple-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-96 overflow-y-auto">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Subscription Status */}
              <div className={`bg-gradient-to-r ${getTierColor(user.subscription_tier)} rounded-lg p-6 text-white`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold capitalize">{user.subscription_tier} Plan</h3>
                    <p className="text-white text-opacity-90 mt-1">
                      {user.subscription_tier === 'free' 
                        ? 'Basic features with ads' 
                        : 'Premium features unlocked'
                      }
                    </p>
                  </div>
                  {getTierIcon(user.subscription_tier)}
                </div>
              </div>

              {/* Usage Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900">API Usage Today</h4>
                  <p className="text-2xl font-bold text-blue-600">
                    {user.daily_api_calls || 0}
                  </p>
                  <p className="text-sm text-blue-700">
                    of {user.max_daily_api_calls?.toLocaleString()} limit
                  </p>
                </div>
                
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="font-medium text-green-900">Account Status</h4>
                  <p className="text-lg font-bold text-green-600">
                    {user.is_active ? 'Active' : 'Inactive'}
                  </p>
                  <p className="text-sm text-green-700">
                    Member since {formatDate(user.created_at)}
                  </p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900">Plan Expires</h4>
                  <p className="text-lg font-bold text-purple-600">
                    {user.subscription_expires_at 
                      ? formatDate(user.subscription_expires_at)
                      : 'Never'
                    }
                  </p>
                  <p className="text-sm text-purple-700">
                    {user.subscription_tier === 'free' ? 'Free forever' : 'Auto-renewal'}
                  </p>
                </div>
              </div>

              {/* API Key */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">API Key</h4>
                  <button
                    onClick={copyApiKey}
                    className="text-sm bg-purple-600 text-white px-3 py-1 rounded hover:bg-purple-700"
                  >
                    Copy
                  </button>
                </div>
                <code className="text-sm bg-white p-2 rounded border block overflow-x-auto">
                  {user.api_key}
                </code>
                <p className="text-xs text-gray-500 mt-2">
                  Use this key to authenticate API requests
                </p>
              </div>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-6">
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  <p className="text-gray-600 mt-2">Loading analytics...</p>
                </div>
              ) : analytics ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900">Total API Calls</h4>
                      <p className="text-2xl font-bold text-blue-600">{analytics.total_api_calls}</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <h4 className="font-medium text-green-900">Videos Accessed</h4>
                      <p className="text-2xl font-bold text-green-600">{analytics.videos_accessed}</p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <h4 className="font-medium text-purple-900">Avg Response Time</h4>
                      <p className="text-2xl font-bold text-purple-600">
                        {analytics.avg_response_time?.toFixed(0)}ms
                      </p>
                    </div>
                  </div>

                  {/* Daily Usage Chart (placeholder) */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-4">Daily Usage</h4>
                    <div className="h-48 bg-gray-100 rounded flex items-center justify-center">
                      <p className="text-gray-500">Usage chart would go here</p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">No analytics data available</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="space-y-6">
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                  <p className="text-gray-600 mt-2">Loading transactions...</p>
                </div>
              ) : (
                <>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Current Plan</h4>
                    <div className="flex justify-between items-center">
                      <span className="capitalize">{user.subscription_tier} Plan</span>
                      <span className="text-green-600 font-medium">
                        {user.subscription_tier === 'free' ? 'Free' : 'Active'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-4">Transaction History</h4>
                    {transactions.length > 0 ? (
                      <div className="space-y-2">
                        {transactions.map((transaction) => (
                          <div key={transaction.id} className="bg-white border rounded-lg p-4">
                            <div className="flex justify-between items-center">
                              <div>
                                <p className="font-medium capitalize">
                                  {transaction.subscription_tier} Plan
                                </p>
                                <p className="text-sm text-gray-600">
                                  {formatDate(transaction.created_at)}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="font-medium">${transaction.amount}</p>
                                <span className={`text-sm px-2 py-1 rounded ${
                                  transaction.status === 'completed' 
                                    ? 'bg-green-100 text-green-600'
                                    : 'bg-yellow-100 text-yellow-600'
                                }`}>
                                  {transaction.status}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-600">No transactions found</p>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-2">Account Settings</h4>
                <p className="text-sm text-yellow-700">
                  Account management features coming soon. For now, contact support for account changes.
                </p>
              </div>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center py-3 border-b">
                  <span className="font-medium">Email Notifications</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                  </label>
                </div>
                
                <div className="flex justify-between items-center py-3 border-b">
                  <span className="font-medium">API Access</span>
                  <span className="text-green-600 font-medium">Enabled</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
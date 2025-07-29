import React, { useState, useEffect } from 'react';
import { Check, Crown, Zap, TrendingUp } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SubscriptionPlans = ({ onSelectPlan, currentUser = null }) => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [billingCycle, setBillingCycle] = useState('monthly');

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscription/plans`);
      setPlans(response.data.plans || []);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPlanIcon = (tier) => {
    switch (tier) {
      case 'free': return '🆓';
      case 'pro': return <Crown className="w-6 h-6 text-yellow-500" />;
      case 'business': return <TrendingUp className="w-6 h-6 text-purple-500" />;
      default: return '📱';
    }
  };

  const getPlanColor = (tier) => {
    switch (tier) {
      case 'free': return 'border-gray-300 bg-gray-50';
      case 'pro': return 'border-yellow-400 bg-gradient-to-br from-yellow-50 to-orange-50';
      case 'business': return 'border-purple-500 bg-gradient-to-br from-purple-50 to-indigo-50';
      default: return 'border-gray-300 bg-white';
    }
  };

  const getPrice = (plan) => {
    if (plan.tier === 'free') return 'Free Forever';
    
    const price = billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly;
    const period = billingCycle === 'yearly' ? 'year' : 'month';
    
    return `$${price.toFixed(2)}/${period}`;
  };

  const getSavings = (plan) => {
    if (plan.tier === 'free' || !plan.savings_percentage) return null;
    
    return billingCycle === 'yearly' ? `Save ${plan.savings_percentage}%` : null;
  };

  const isCurrentPlan = (planTier) => {
    return currentUser?.subscription_tier === planTier;
  };

  const isPlanUpgrade = (planTier) => {
    if (!currentUser) return true;
    
    const tierOrder = { free: 0, pro: 1, business: 2 };
    return tierOrder[planTier] > tierOrder[currentUser.subscription_tier];
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-300 rounded mb-4"></div>
            <div className="h-8 bg-gray-300 rounded mb-4"></div>
            <div className="space-y-2">
              {[...Array(5)].map((_, j) => (
                <div key={j} className="h-4 bg-gray-300 rounded"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Billing Toggle */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingCycle === 'monthly'
                ? 'bg-white text-purple-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingCycle === 'yearly'
                ? 'bg-white text-purple-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Yearly
            <span className="ml-1 text-xs bg-green-100 text-green-600 px-1 rounded">
              Save up to 17%
            </span>
          </button>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.tier}
            className={`relative rounded-2xl border-2 p-6 transition-all duration-300 hover:scale-105 hover:shadow-xl ${getPlanColor(plan.tier)} ${
              plan.tier === 'pro' ? 'ring-2 ring-yellow-400 ring-opacity-50' : ''
            }`}
          >
            {/* Most Popular Badge */}
            {plan.tier === 'pro' && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  ⭐ Most Popular
                </span>
              </div>
            )}

            {/* Current Plan Badge */}
            {isCurrentPlan(plan.tier) && (
              <div className="absolute -top-3 right-4">
                <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                  Current Plan
                </span>
              </div>
            )}

            <div className="text-center mb-6">
              <div className="flex justify-center mb-3">
                {getPlanIcon(plan.tier)}
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
              <div className="mb-2">
                <span className="text-3xl font-bold text-gray-900">{getPrice(plan)}</span>
                {getSavings(plan) && (
                  <div className="text-sm text-green-600 font-medium mt-1">
                    {getSavings(plan)}
                  </div>
                )}
              </div>
            </div>

            {/* Features List */}
            <div className="space-y-3 mb-6">
              {plan.features.map((feature, index) => (
                <div key={index} className="flex items-start">
                  <Check className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{feature}</span>
                </div>
              ))}
            </div>

            {/* Action Button */}
            <button
              onClick={() => onSelectPlan(plan, billingCycle)}
              disabled={isCurrentPlan(plan.tier)}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                isCurrentPlan(plan.tier)
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : plan.tier === 'free'
                  ? 'bg-gray-800 text-white hover:bg-gray-900'
                  : plan.tier === 'pro'
                  ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white hover:from-yellow-500 hover:to-orange-600'
                  : 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white hover:from-purple-600 hover:to-indigo-700'
              }`}
            >
              {isCurrentPlan(plan.tier)
                ? 'Current Plan'
                : plan.tier === 'free'
                ? 'Get Started Free'
                : isPlanUpgrade(plan.tier)
                ? `Upgrade to ${plan.name}`
                : `Switch to ${plan.name}`
              }
            </button>

            {/* Trial Info */}
            {plan.tier !== 'free' && (
              <p className="text-xs text-gray-500 text-center mt-3">
                30-day money-back guarantee
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Features Comparison */}
      <div className="mt-12 bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">
          Detailed Feature Comparison
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4">Feature</th>
                <th className="text-center py-3 px-4">Free</th>
                <th className="text-center py-3 px-4">Pro</th>
                <th className="text-center py-3 px-4">Business</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              <tr>
                <td className="py-3 px-4">Daily viral videos</td>
                <td className="text-center py-3 px-4">10</td>
                <td className="text-center py-3 px-4">Unlimited</td>
                <td className="text-center py-3 px-4">Unlimited</td>
              </tr>
              <tr>
                <td className="py-3 px-4">API calls per day</td>
                <td className="text-center py-3 px-4">100</td>
                <td className="text-center py-3 px-4">10,000</td>
                <td className="text-center py-3 px-4">100,000</td>
              </tr>
              <tr>
                <td className="py-3 px-4">Advertisements</td>
                <td className="text-center py-3 px-4">Yes</td>
                <td className="text-center py-3 px-4">No</td>
                <td className="text-center py-3 px-4">No</td>
              </tr>
              <tr>
                <td className="py-3 px-4">Analytics dashboard</td>
                <td className="text-center py-3 px-4">❌</td>
                <td className="text-center py-3 px-4">Basic</td>
                <td className="text-center py-3 px-4">Advanced</td>
              </tr>
              <tr>
                <td className="py-3 px-4">Priority support</td>
                <td className="text-center py-3 px-4">❌</td>
                <td className="text-center py-3 px-4">Email</td>
                <td className="text-center py-3 px-4">Priority</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPlans;
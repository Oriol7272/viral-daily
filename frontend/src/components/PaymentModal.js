import React, { useState } from 'react';
import { X, CreditCard, Shield, Clock } from 'lucide-react';
import axios from 'axios';
import PayPalPaymentButton from './PayPalPaymentButton';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PaymentModal = ({ isOpen, onClose, selectedPlan, billingCycle, user }) => {
  const [processing, setProcessing] = useState(false);
  const [email, setEmail] = useState(user?.email || '');
  const [paymentMethod, setPaymentMethod] = useState('stripe'); // 'stripe' or 'paypal'
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [paymentError, setPaymentError] = useState(null);
  
  if (!isOpen || !selectedPlan) return null;

  const handleStripePayment = async () => {
    if (!email) {
      alert('Please enter your email address');
      return;
    }

    setProcessing(true);
    setPaymentError(null);
    
    try {
      // Create checkout session
      const checkoutData = {
        subscription_tier: selectedPlan.tier,
        billing_cycle: billingCycle,
        email: email
      };

      const response = await axios.post(`${API}/payments/v1/checkout/session`, checkoutData, {
        headers: user?.api_key ? { 'Authorization': `Bearer ${user.api_key}` } : {}
      });

      // Redirect to Stripe Checkout
      if (response.data.url) {
        window.location.href = response.data.url;
      } else {
        throw new Error('No checkout URL received');
      }
    } catch (error) {
      console.error('Payment error:', error);
      setPaymentError('Failed to initiate Stripe payment. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const handlePayPalSuccess = (paymentData) => {
    setPaymentSuccess(true);
    setPaymentError(null);
    
    // Show success message and close modal after delay
    setTimeout(() => {
      alert(`Payment successful! Welcome to ${selectedPlan.name}! 🎉`);
      onClose();
      // Refresh page to reflect new subscription
      window.location.reload();
    }, 2000);
  };

  const handlePayPalError = (errorMessage) => {
    setPaymentError(errorMessage);
    setPaymentSuccess(false);
  };

  const getPrice = () => {
    const price = billingCycle === 'yearly' ? selectedPlan.price_yearly : selectedPlan.price_monthly;
    return price.toFixed(2);
  };

  const getSavings = () => {
    if (billingCycle === 'yearly' && selectedPlan.savings_percentage) {
      return `Save ${selectedPlan.savings_percentage}% annually`;
    }
    return null;
  };

  if (paymentSuccess) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl p-6 w-full max-w-md text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-green-600 mb-2">Payment Successful!</h2>
          <p className="text-gray-600 mb-4">
            Welcome to {selectedPlan.name}! Your subscription is now active.
          </p>
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600 mx-auto"></div>
          <p className="text-sm text-gray-500 mt-2">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md relative max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <CreditCard className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Upgrade to {selectedPlan.name}</h2>
          <p className="text-gray-600 mt-2">Choose your preferred payment method</p>
        </div>

        {/* Plan Summary */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="font-medium text-gray-900">{selectedPlan.name} Plan</span>
            <span className="text-2xl font-bold text-gray-900">${getPrice()}</span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Billed {billingCycle}</span>
            {getSavings() && (
              <span className="text-green-600 font-medium">{getSavings()}</span>
            )}
          </div>
        </div>

        {/* Email Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            required
          />
        </div>

        {/* Payment Method Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Choose Payment Method
          </label>
          <div className="space-y-3">
            <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="paymentMethod"
                value="stripe"
                checked={paymentMethod === 'stripe'}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="mr-3"
              />
              <div className="flex items-center">
                <CreditCard className="w-5 h-5 text-gray-600 mr-2" />
                <span>Credit Card (Stripe)</span>
                <div className="ml-auto flex space-x-1">
                  <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">VISA</span>
                  <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded">MC</span>
                </div>
              </div>
            </label>
            
            <label className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="paymentMethod"
                value="paypal"
                checked={paymentMethod === 'paypal'}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="mr-3"
              />
              <div className="flex items-center">
                <div className="w-5 h-5 bg-blue-600 rounded mr-2 flex items-center justify-center">
                  <span className="text-white text-xs font-bold">P</span>
                </div>
                <span>PayPal</span>
                <span className="ml-auto text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">Secure</span>
              </div>
            </label>
          </div>
        </div>

        {/* Error Message */}
        {paymentError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{paymentError}</p>
          </div>
        )}

        {/* Payment Buttons */}
        <div className="space-y-3">
          {paymentMethod === 'stripe' ? (
            <button
              onClick={handleStripePayment}
              disabled={processing || !email}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-4 rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {processing ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Processing...
                </div>
              ) : (
                `Pay with Stripe - $${getPrice()}/${billingCycle === 'yearly' ? 'year' : 'month'}`
              )}
            </button>
          ) : (
            <div className="w-full">
              <PayPalPaymentButton
                selectedPlan={selectedPlan}
                billingCycle={billingCycle}
                user={user || { email }}
                onSuccess={handlePayPalSuccess}
                onError={handlePayPalError}
              />
            </div>
          )}
          
          <button
            onClick={onClose}
            className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
        </div>

        {/* Features Highlight */}
        <div className="mt-6">
          <h3 className="font-medium text-gray-900 mb-3">What you'll get:</h3>
          <div className="space-y-2">
            {selectedPlan.features.slice(0, 4).map((feature, index) => (
              <div key={index} className="flex items-center text-sm text-gray-600">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                {feature}
              </div>
            ))}
          </div>
        </div>

        {/* Security & Guarantees */}
        <div className="mt-6 space-y-2">
          <div className="flex items-center text-sm text-gray-600">
            <Shield className="w-4 h-4 mr-2 text-green-500" />
            Secure payment processing
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <Clock className="w-4 h-4 mr-2 text-blue-500" />
            30-day money-back guarantee
          </div>
        </div>

        {/* Terms */}
        <p className="text-xs text-gray-500 text-center mt-4">
          By subscribing, you agree to our Terms of Service and Privacy Policy. 
          You can cancel anytime from your account settings.
        </p>
      </div>
    </div>
  );
};

export default PaymentModal;
import React, { useState, useEffect } from 'react';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import { AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PayPalPaymentButton = ({ selectedPlan, billingCycle, user, onSuccess, onError }) => {
  const [paypalConfig, setPaypalConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPayPalConfig();
  }, []);

  const fetchPayPalConfig = async () => {
    try {
      const response = await axios.get(`${API}/payments/paypal/config`);
      setPaypalConfig(response.data);
    } catch (error) {
      console.error('Error fetching PayPal config:', error);
      setError('PayPal is not available at the moment');
    } finally {
      setLoading(false);
    }
  };

  const createOrder = async () => {
    try {
      const orderData = {
        subscription_tier: selectedPlan.tier,
        billing_cycle: billingCycle,
        email: user?.email
      };

      const headers = {};
      if (user?.api_key) {
        headers['Authorization'] = `Bearer ${user.api_key}`;
      }

      const response = await axios.post(`${API}/payments/paypal/create-order`, orderData, { headers });
      
      return response.data.order_id;
    } catch (error) {
      console.error('Error creating PayPal order:', error);
      onError && onError('Failed to create PayPal payment');
      throw error;
    }
  };

  const onApprove = async (data) => {
    try {
      const response = await axios.post(`${API}/payments/paypal/capture-order/${data.orderID}`);
      
      if (response.data.status === 'COMPLETED') {
        onSuccess && onSuccess({
          orderId: data.orderID,
          captureId: response.data.capture_id,
          amount: response.data.amount,
          currency: response.data.currency,
          method: 'paypal'
        });
      } else {
        onError && onError('Payment was not completed');
      }
    } catch (error) {
      console.error('Error capturing PayPal order:', error);
      onError && onError('Failed to complete PayPal payment');
    }
  };

  const onCancel = () => {
    onError && onError('Payment was cancelled');
  };

  const onPayPalError = (error) => {
    console.error('PayPal error:', error);
    onError && onError('PayPal payment failed');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading PayPal...</span>
      </div>
    );
  }

  if (error || !paypalConfig || !paypalConfig.client_id) {
    return (
      <div className="flex items-center p-4 bg-gray-100 rounded-lg">
        <AlertCircle className="w-5 h-5 text-gray-500 mr-2" />
        <span className="text-gray-600">PayPal payments are not available</span>
      </div>
    );
  }

  const paypalOptions = {
    "client-id": paypalConfig.client_id,
    currency: paypalConfig.currency || "USD",
    intent: "capture",
    "disable-funding": "credit,card"
  };

  return (
    <div className="paypal-button-container">
      <PayPalScriptProvider options={paypalOptions}>
        <PayPalButtons
          style={{
            layout: "vertical",
            color: "blue",
            shape: "rect",
            label: "paypal"
          }}
          createOrder={createOrder}
          onApprove={onApprove}
          onCancel={onCancel}
          onError={onPayPalError}
          forceReRender={[selectedPlan, billingCycle, user]}
        />
      </PayPalScriptProvider>
    </div>
  );
};

export default PayPalPaymentButton;
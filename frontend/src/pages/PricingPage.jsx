import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ArrowLeft, CreditCard, Wallet, Smartphone, Landmark } from 'lucide-react';
import apiClient from '../api/client';

const PLANS = [
    {
        id: 1,
        name: 'free',
        title: 'Free Plan',
        price: '0',
        features: ['1 file per day', 'Basic conversions', 'Standard speed'],
        buttonText: 'Current Plan',
        disabled: true,
    },
    {
        id: 2,
        name: 'hourly',
        title: 'Hourly Session',
        price: '7.5',
        features: ['3 files included', '1 hour session', 'Priority processing'],
        buttonText: 'Buy 1 Hour',
        disabled: false,
    },
    {
        id: 3,
        name: 'monthly',
        title: 'Monthly Pro',
        price: '69',
        features: ['No daily limits', '30 days duration', 'Turbo speed', 'Cloud storage'],
        buttonText: 'Go Pro',
        disabled: false,
    }
];

const METHODS = [
    { id: 'card', name: 'Card', icon: <CreditCard className="w-5 h-5" /> },
    { id: 'wallet', name: 'Wallet / Vodafone Cash', icon: <Smartphone className="w-5 h-5" /> },
    { id: 'instapay', name: 'InstaPay', icon: <Smartphone className="w-5 h-5" /> },
    { id: 'fawry', name: 'Fawry', icon: <Landmark className="w-5 h-5" /> },
];

const PricingPage = () => {
    const [selectedPlan, setSelectedPlan] = useState(null);
    const [selectedMethod, setSelectedMethod] = useState('card');
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    const handleBuy = async (planId) => {
        setLoading(true);
        try {
            const res = await apiClient.post('/payments/initiate', {
                plan_id: planId,
                method: selectedMethod,
            });

            if (res.data.payment_url) {
                window.location.href = res.data.payment_url;
            }
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to initiate payment');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-6">
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center text-gray-600 hover:text-primary-600 mb-8 font-medium transition-colors"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Dashboard
                </button>

                <div className="text-center mb-12">
                    <h1 className="text-4xl font-extrabold text-gray-900 mb-4">Choose Your Plan</h1>
                    <p className="text-lg text-gray-600">Upgrade to convert more files faster</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                    {PLANS.map((plan) => (
                        <div
                            key={plan.id}
                            className={`bg-white rounded-2xl p-8 shadow-lg border-2 transition-all
                ${selectedPlan === plan.id ? 'border-primary-500 scale-[1.02]' : 'border-transparent'}`}
                            onClick={() => !plan.disabled && setSelectedPlan(plan.id)}
                        >
                            <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.title}</h3>
                            <div className="flex items-baseline mb-6">
                                <span className="text-3xl font-extrabold text-gray-900">{plan.price}</span>
                                <span className="text-gray-500 ml-1">EGP</span>
                            </div>
                            <ul className="space-y-4 mb-8">
                                {plan.features.map((feature, i) => (
                                    <li key={i} className="flex items-start text-sm text-gray-600">
                                        <Check className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>
                            <button
                                disabled={plan.disabled || loading}
                                onClick={(e) => { e.stopPropagation(); handleBuy(plan.id); }}
                                className={`w-full py-3 rounded-xl font-bold transition-all
                  ${plan.disabled
                                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                        : 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-200 active:scale-[0.98]'}`}
                            >
                                {loading && selectedPlan === plan.id ? 'Processing...' : plan.buttonText}
                            </button>
                        </div>
                    ))}
                </div>

                {/* Payment Methods */}
                <div className="bg-white rounded-2xl p-8 shadow-md border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center">
                        <CreditCard className="w-5 h-5 mr-3 text-primary-600" />
                        Select Payment Method
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        {METHODS.map((method) => (
                            <button
                                key={method.id}
                                onClick={() => setSelectedMethod(method.id)}
                                className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all
                  ${selectedMethod === method.id
                                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                                        : 'border-gray-100 bg-gray-50 text-gray-500 hover:border-gray-200'}`}
                            >
                                <div className="mb-2">{method.icon}</div>
                                <span className="text-xs font-bold">{method.name}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PricingPage;

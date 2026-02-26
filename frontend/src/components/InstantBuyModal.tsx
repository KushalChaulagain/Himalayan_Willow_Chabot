import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ProductCard as ProductCardType } from '../types';
import { useChatContext } from '../contexts/ChatContext';
import { loadProfile, saveProfile } from '../utils/userProfile';

interface InstantBuyModalProps {
  product: ProductCardType;
  onClose: () => void;
}

type PaymentMethod = 'esewa' | 'khalti' | 'cod';

const PAYMENT_METHODS: Array<{ id: PaymentMethod; label: string; icon: string; description: string }> = [
  { id: 'esewa', label: 'eSewa', icon: '💚', description: 'Pay via eSewa wallet' },
  { id: 'khalti', label: 'Khalti', icon: '💜', description: 'Pay via Khalti wallet' },
  { id: 'cod', label: 'Cash on Delivery', icon: '💵', description: 'Pay when you receive' },
];

const InstantBuyModal: React.FC<InstantBuyModalProps> = ({ product, onClose }) => {
  const { apiClient, sessionId, addBotMessage } = useChatContext();
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(null);
  const [phone, setPhone] = useState('');
  const [city, setCity] = useState('');
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const profile = loadProfile();
    if (profile) {
      if (profile.phone) setPhone(profile.phone);
      if (profile.city) setCity(profile.city);
    }
  }, []);

  const handleConfirm = async () => {
    if (!paymentMethod) { setError('Please select a payment method'); return; }
    if (!phone || phone.length < 10) { setError('Please enter a valid phone number'); return; }
    if (!city.trim()) { setError('Please enter your city'); return; }

    setError('');
    setLoading(true);

    saveProfile({ phone, city });

    try {
      const result = await apiClient.createOrder({
        session_id: sessionId || `temp-${Date.now()}`,
        payment_method: paymentMethod,
        customer_phone: phone,
        delivery_address: { city, address, country: 'Nepal' },
        items: [{
          product_id: product.id,
          product_name: product.name,
          product_sku: `SKU-${product.id}`,
          unit_price: product.price,
          quantity: 1,
          subtotal: product.price,
        }],
      });

      if (result) {
        onClose();
        addBotMessage(
          `Great choice, Skipper! Your order for ${product.name} has been placed.\n\nOrder ID: ${result.order_id}\nTotal: NPR ${result.total_amount.toLocaleString()}\nPayment: ${paymentMethod.toUpperCase()}\n\nYour gear is heading to the pavilion!`,
          {
            interactiveContent: {
              type: 'confetti',
              confettiMessage: `Order ${result.order_id} confirmed!`,
            },
            quickReplies: ['Track my order', 'Continue shopping', 'Talk to human'],
          }
        );
      } else {
        setError('Order creation failed. Please try again.');
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ y: '100%', opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: '100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="relative bg-[#1A1A1A] border border-white/10 rounded-t-2xl sm:rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto z-10"
        >
          {/* Handle bar */}
          <div className="flex justify-center pt-3 pb-1 sm:hidden">
            <div className="w-10 h-1 bg-white/20 rounded-full" />
          </div>

          <div className="p-5">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Quick Checkout</h3>
              <button
                onClick={onClose}
                className="p-1 text-white/50 hover:text-white transition-colors"
                aria-label="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Product summary */}
            <div className="flex gap-3 bg-white/5 border border-white/10 rounded-lg p-3 mb-4">
              <div className="w-16 h-16 rounded-md overflow-hidden bg-[#262626] flex-shrink-0">
                {product.image_url ? (
                  <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-2xl opacity-50">
                    {'\u{1F3CF}'}
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-white truncate">{product.name}</h4>
                <p className="text-lg font-bold text-white mt-1">
                  NPR {product.price.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Payment method selection */}
            <div className="mb-4">
              <label className="text-sm text-white/70 font-medium block mb-2">Payment Method</label>
              <div className="grid grid-cols-3 gap-2">
                {PAYMENT_METHODS.map((pm) => (
                  <button
                    key={pm.id}
                    onClick={() => setPaymentMethod(pm.id)}
                    className={`flex flex-col items-center p-3 rounded-lg border transition-all ${
                      paymentMethod === pm.id
                        ? 'border-white/40 bg-white/10'
                        : 'border-white/10 bg-white/5 hover:border-white/20'
                    }`}
                  >
                    <span className="text-xl mb-1">{pm.icon}</span>
                    <span className="text-xs font-semibold text-white">{pm.label}</span>
                    <span className="text-[10px] text-white/40 mt-0.5 text-center">{pm.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Delivery info */}
            <div className="space-y-3 mb-4">
              <div>
                <label htmlFor="buy-phone" className="text-sm text-white/70 font-medium block mb-1">Phone Number</label>
                <input
                  id="buy-phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="98XXXXXXXX"
                  className="w-full bg-[#262626] border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/30 text-sm"
                />
              </div>
              <div>
                <label htmlFor="buy-city" className="text-sm text-white/70 font-medium block mb-1">City</label>
                <input
                  id="buy-city"
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Kathmandu"
                  className="w-full bg-[#262626] border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/30 text-sm"
                />
              </div>
              <div>
                <label htmlFor="buy-address" className="text-sm text-white/70 font-medium block mb-1">
                  Address <span className="text-white/30">(optional)</span>
                </label>
                <input
                  id="buy-address"
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Street, area..."
                  className="w-full bg-[#262626] border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-white/30 text-sm"
                />
              </div>
            </div>

            {error && (
              <p className="text-xs text-red-400 mb-3">{error}</p>
            )}

            {/* Confirm button */}
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-60 disabled:cursor-wait text-white py-3 rounded-lg font-bold text-sm transition-colors"
            >
              {loading ? 'Processing...' : `Confirm & Pay NPR ${product.price.toLocaleString()}`}
            </button>

            <p className="text-[10px] text-white/30 text-center mt-3">
              Free delivery across Nepal. Secure payment processing.
            </p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default InstantBuyModal;

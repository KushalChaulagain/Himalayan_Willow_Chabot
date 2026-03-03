import { AnimatePresence, motion } from "framer-motion";
import React, { useEffect, useState } from "react";
import { useChatContext } from "../contexts/ChatContext";
import EsewaIcon from "../images/Esewa_icon.svg";
import KhaltiIcon from "../images/Khalti_icon.svg";
import { ProductCard as ProductCardType } from "../types";
import { loadProfile, saveProfile } from "../utils/userProfile";

interface InstantBuyModalProps {
  product: ProductCardType;
  onClose: () => void;
}

type PaymentMethod = "esewa" | "khalti" | "cod";

const NEPAL_MOBILE_PREFIXES = ["984", "980", "981"];

const isValidNepalPhone = (phone: string): boolean => {
  const cleaned = phone.replace(/\D/g, "");
  if (cleaned.length !== 10) return false;
  return NEPAL_MOBILE_PREFIXES.some((p) => cleaned.startsWith(p));
};

const PAYMENT_METHODS: Array<{
  id: PaymentMethod;
  label: string;
  icon: string;
  description: string;
}> = [
  {
    id: "esewa",
    label: "eSewa",
    icon: EsewaIcon,
    description: "Pay via eSewa wallet",
  },
  {
    id: "khalti",
    label: "Khalti",
    icon: KhaltiIcon,
    description: "Pay via Khalti wallet",
  },
  {
    id: "cod",
    label: "Cash on Delivery",
    icon: "/payments/cod.svg",
    description: "Pay when you receive",
  },
];

const InstantBuyModal: React.FC<InstantBuyModalProps> = ({
  product,
  onClose,
}) => {
  const { apiClient, sessionId, addBotMessage } = useChatContext();
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(
    null,
  );
  const [phone, setPhone] = useState("");
  const [city, setCity] = useState("");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const profile = loadProfile();
    if (profile) {
      if (profile.phone) setPhone(profile.phone);
      if (profile.city) setCity(profile.city);
      if (profile.address) setAddress(profile.address);
    }
  }, []);

  const getButtonLabel = (): string => {
    if (loading) return "Processing...";
    if (paymentMethod === "cod") return "Complete Order";
    if (paymentMethod === "esewa")
      return `Pay with eSewa — NPR ${product.price.toLocaleString()}`;
    if (paymentMethod === "khalti")
      return `Pay with Khalti — NPR ${product.price.toLocaleString()}`;
    return `Confirm & Pay NPR ${product.price.toLocaleString()}`;
  };

  const handleConfirm = async () => {
    if (!paymentMethod) {
      setError("Please select a payment method");
      return;
    }
    if (!isValidNepalPhone(phone)) {
      setError("Enter a valid Nepal mobile number (984/980/981)");
      return;
    }
    if (!city.trim()) {
      setError("Please enter your city");
      return;
    }
    if (!address.trim()) {
      setError("Please enter your delivery address");
      return;
    }

    setError("");
    setLoading(true);

    saveProfile({ phone, city, address: address.trim() });

    try {
      const result = await apiClient.createOrder({
        session_id: sessionId || `temp-${Date.now()}`,
        payment_method: paymentMethod,
        customer_phone: phone,
        delivery_address: {
          city,
          address: address.trim(),
          street: address.trim(),
          country: "Nepal",
        },
        items: [
          {
            product_id: product.id,
            product_name: product.name,
            product_sku: `SKU-${product.id}`,
            unit_price: Math.round(product.price * 100),
            quantity: 1,
            subtotal: Math.round(product.price * 100),
          },
        ],
      });

      if ("error" in result) {
        setError(result.error);
      } else {
        onClose();
        addBotMessage(
          `Great choice, Skipper! Your order for ${product.name} has been placed.\n\nOrder ID: ${result.order_id}\nTotal: NPR ${result.total_amount.toLocaleString()}\nPayment: ${paymentMethod.toUpperCase()}\n\nYour gear is heading to the pavilion!`,
          {
            interactiveContent: {
              type: "confetti",
              confettiMessage: `Order ${result.order_id} confirmed!`,
            },
            quickReplies: [
              "Track my order",
              "Continue shopping",
              "Talk to human",
            ],
          },
        );
      }
    } catch {
      setError("Something went wrong. Please try again.");
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
          initial={{ y: "100%", opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: "100%", opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative bg-[#1A1A1A] border border-white/10 rounded-t-2xl sm:rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto z-10 shadow-card-2"
        >
          {/* Handle bar */}
          <div className="flex justify-center pt-3 pb-1 sm:hidden">
            <div className="w-10 h-1 bg-white/20 rounded-full" />
          </div>

          <div className="p-5">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Quick Checkout</h3>
              </div>
              <button
                onClick={onClose}
                className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-white/50 hover:text-white transition-colors -mr-2"
                aria-label="Close"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* Product summary */}
            <div className="flex gap-3 bg-white/5 border border-white/10 rounded-lg p-3 mb-4">
              <div className="w-16 h-16 rounded-md overflow-hidden bg-[#262626] flex-shrink-0">
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-2xl opacity-50">
                    {"\u{1F3CF}"}
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-white truncate">
                  {product.name}
                </h4>
                <p className="text-lg font-bold text-white mt-1">
                  NPR {product.price.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Payment method selection */}
            <div className="mb-4">
              <label className="text-sm text-white/90 font-medium block mb-2">
                Payment Method
              </label>
              <div className="grid grid-cols-3 gap-2">
                {PAYMENT_METHODS.map((pm) => (
                  <button
                    key={pm.id}
                    onClick={() => setPaymentMethod(pm.id)}
                    className={`flex flex-col items-center justify-center p-3 min-h-[44px] rounded-lg border transition-all ${
                      paymentMethod === pm.id
                        ? "border-white/40 bg-white/10 shadow-default"
                        : "border-white/10 bg-white/5 hover:border-white/20"
                    }`}
                  >
                    {/\.(svg|png|webp)$/i.test(pm.icon) ? (
                      <img
                        src={pm.icon}
                        alt={pm.label}
                        className="w-10 h-10 object-contain mb-1"
                      />
                    ) : (
                      <span className="text-xl mb-1">{pm.icon}</span>
                    )}
                    <span className="text-xs font-semibold text-white">
                      {pm.label}
                    </span>
                    <span className="text-[10px] text-white/40 mt-0.5 text-center">
                      {pm.description}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Delivery info */}
            <div className="space-y-4 mb-4">
              <div>
                <label
                  htmlFor="buy-phone"
                  className="mb-3 block text-sm font-medium text-white/90"
                >
                  Phone Number
                </label>
                <input
                  id="buy-phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="10 digits, e.g. 9841234567"
                  className="w-full rounded-lg border-[1.5px] border-stroke bg-[#262626] py-3 px-5 font-medium text-white placeholder-white/50 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30 disabled:cursor-default disabled:opacity-50"
                />
              </div>
              <div>
                <label
                  htmlFor="buy-city"
                  className="mb-3 block text-sm font-medium text-white/90"
                >
                  City
                </label>
                <input
                  id="buy-city"
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Kathmandu"
                  className="w-full rounded-lg border-[1.5px] border-stroke bg-[#262626] py-3 px-5 font-medium text-white placeholder-white/50 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30 disabled:cursor-default disabled:opacity-50"
                />
              </div>
              <div>
                <label
                  htmlFor="buy-address"
                  className="mb-3 block text-sm font-medium text-white/90"
                >
                  Delivery Address <span className="text-amber-400">*</span>
                </label>
                <input
                  id="buy-address"
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Street, area, ward..."
                  required
                  aria-required="true"
                  aria-invalid={!!error && error.includes("address")}
                  aria-describedby={error ? "checkout-error" : undefined}
                  className="w-full rounded-lg border-[1.5px] border-stroke bg-[#262626] py-3 px-5 font-medium text-white placeholder-white/50 outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30 disabled:cursor-default disabled:opacity-50"
                />
              </div>
            </div>

            {/* Delivery summary */}
            <div className="text-xs text-white/80 mb-4 py-2 px-3 bg-white/5 rounded-lg border border-white/10">
              Delivery: Free · Est. Arrival: 2–4 days (Valley) / 5–7 days
              (outside)
            </div>

            {error && (
              <div
                id="checkout-error"
                role="alert"
                className="mb-4 flex border-l-6 border-red-500 bg-red-500/10 px-4 py-3 rounded-r"
              >
                <p className="text-sm text-red-400 leading-relaxed">{error}</p>
              </div>
            )}

            {/* Confirm button */}
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="w-full min-h-[44px] bg-amber-500 hover:bg-amber-400 active:scale-[0.98] disabled:opacity-60 disabled:cursor-wait text-[#1A1A1A] py-3 rounded-lg font-bold text-sm transition-colors"
            >
              {getButtonLabel()}
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

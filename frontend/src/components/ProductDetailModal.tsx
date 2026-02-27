import React, { lazy, Suspense } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ProductCard as ProductCardType } from "../types";
import { useChatContext } from "../contexts/ChatContext";

const InstantBuyModal = lazy(() => import("./InstantBuyModal"));

const CATEGORY_ICONS: Record<string, string> = {
  bat: "\u{1F3CF}",
  ball: "\u{26BE}",
  gloves: "\u{1F9E4}",
  pads: "\u{1F9B5}",
  helmet: "\u{26D1}",
  shoes: "\u{1F45F}",
  kit_bag: "\u{1F392}",
};

interface ProductDetailModalProps {
  product: ProductCardType;
  onClose: () => void;
}

function StarRating({ rating, count }: { rating: number; count?: number }) {
  const fullStars = Math.floor(rating);
  const hasHalf = rating - fullStars >= 0.3;
  return (
    <div className="flex items-center gap-1">
      <div className="flex">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-4 h-4 ${
              star <= fullStars
                ? "text-amber-400"
                : star === fullStars + 1 && hasHalf
                  ? "text-amber-400/50"
                  : "text-white/20"
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
      {count !== undefined && (
        <span className="text-sm text-white/50">({count})</span>
      )}
    </div>
  );
}

const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  product,
  onClose,
}) => {
  const { addToCart, sendMessage } = useChatContext();
  const [showBuyModal, setShowBuyModal] = React.useState(false);
  const category = product.category || "bat";
  const icon = CATEGORY_ICONS[category] || "\u{1F3CF}";
  const gradient =
    {
      bat: "from-amber-900/40 to-amber-800/20",
      ball: "from-red-900/40 to-red-800/20",
      gloves: "from-blue-900/40 to-blue-800/20",
      pads: "from-green-900/40 to-green-800/20",
      helmet: "from-purple-900/40 to-purple-800/20",
      shoes: "from-cyan-900/40 to-cyan-800/20",
      kit_bag: "from-orange-900/40 to-orange-800/20",
    }[category] || "from-gray-900/40 to-gray-800/20";

  const specs = product.specifications || {};
  const hasMultipleImages = product.images && product.images.length > 1;

  const handleAddToCart = () => {
    addToCart(product.id);
    sendMessage(`Add ${product.name} to cart`);
  };

  return (
    <>
      <AnimatePresence>
        <div className="fixed inset-0 z-[55] flex items-end sm:items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60"
            onClick={onClose}
          />

          <motion.div
            initial={{ y: "100%", opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "100%", opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative bg-[#1A1A1A] border border-white/10 rounded-t-2xl sm:rounded-2xl w-full max-w-lg max-h-[90vh] flex flex-col z-10"
          >
            <div className="flex justify-center pt-3 pb-1 sm:hidden">
              <div className="w-10 h-1 bg-white/20 rounded-full" />
            </div>

            <div className="flex-1 overflow-y-auto min-h-0">
              <div className="p-5 pb-32">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-bold text-white pr-8">{product.name}</h3>
                  <button
                    onClick={onClose}
                    className="p-1 text-white/50 hover:text-white transition-colors -mr-2 -mt-1"
                    aria-label="Close"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Image area - 360-style carousel if multiple images */}
                <div
                  className={`relative w-full aspect-[4/3] rounded-xl overflow-hidden bg-gradient-to-br ${gradient} mb-4`}
                >
                  {hasMultipleImages ? (
                    <div className="flex overflow-x-auto snap-x snap-mandatory gap-0 h-full">
                      {product.images!.map((imgSrc, idx) => (
                        <div
                          key={idx}
                          className="flex-shrink-0 w-full h-full snap-center"
                        >
                          <img
                            src={imgSrc}
                            alt={`${product.name} - angle ${idx + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ))}
                    </div>
                  ) : product.image_url ? (
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-6xl opacity-50">{icon}</span>
                    </div>
                  )}
                  {hasMultipleImages && (
                    <span className="absolute bottom-2 right-2 text-[10px] text-white/60 bg-black/40 px-2 py-0.5 rounded">
                      Spin to view
                    </span>
                  )}
                </div>

                {/* Price & rating */}
                <div className="flex items-center justify-between gap-4 mb-3">
                  <span className="text-2xl font-bold text-white">
                    NPR {product.price.toLocaleString()}
                  </span>
                  {product.rating !== undefined && (
                    <StarRating rating={product.rating} count={product.review_count} />
                  )}
                </div>

                <span className="text-[10px] text-amber-400/90 font-medium px-1.5 py-0.5 rounded-full border border-amber-400/40 bg-amber-400/10 inline-block mb-3">
                  30-Day Game-Ready Guarantee
                </span>

                {product.description && (
                  <p className="text-sm text-white/70 mb-4 leading-relaxed">
                    {product.description}
                  </p>
                )}

                {/* Specifications */}
                {Object.keys(specs).length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-white/50 uppercase tracking-wide">
                      Specifications
                    </h4>
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                      {Object.entries(specs)
                        .filter(([k]) => !["images", "audio_url"].includes(k))
                        .map(([key, value]) => (
                          <React.Fragment key={key}>
                            <dt className="text-white/50 capitalize">
                              {key.replace(/_/g, " ")}
                            </dt>
                            <dd className="text-white">{String(value)}</dd>
                          </React.Fragment>
                        ))}
                    </dl>
                  </div>
                )}

                {product.in_stock && (
                  <div className="mt-3 flex items-center gap-1 text-amber-400/90 text-sm">
                    <span className="w-2 h-2 bg-amber-400 rounded-full" />
                    In Stock
                  </div>
                )}
              </div>
            </div>

            {/* Sticky footer - Add to Cart & Buy Now always visible */}
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-[#1A1A1A] border-t border-white/10 rounded-b-2xl">
              <div className="flex gap-2">
                <button
                  onClick={handleAddToCart}
                  disabled={!product.in_stock}
                  className="flex-1 bg-white hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed text-[#1A1A1A] py-3 rounded-lg font-semibold text-sm transition-colors min-h-[44px]"
                >
                  Add to Cart
                </button>
                <button
                  onClick={() => setShowBuyModal(true)}
                  disabled={!product.in_stock}
                  className="flex-1 bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-[#1A1A1A] py-3 rounded-lg font-bold text-sm transition-colors min-h-[44px]"
                >
                  Buy Now
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </AnimatePresence>

      {showBuyModal && (
        <Suspense fallback={null}>
          <InstantBuyModal
            product={product}
            onClose={() => setShowBuyModal(false)}
          />
        </Suspense>
      )}
    </>
  );
};

export default ProductDetailModal;

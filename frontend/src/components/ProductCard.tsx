import React, { lazy, Suspense, useState } from "react";
import "swiper/css";
import "swiper/css/pagination";
import { Pagination } from "swiper/modules";
import { Swiper, SwiperSlide } from "swiper/react";
import { useChatContext } from "../contexts/ChatContext";
import { ProductCard as ProductCardType } from "../types";
import AudioPlayer from "./AudioPlayer";

const InstantBuyModal = lazy(() => import("./InstantBuyModal"));
const ProductDetailModal = lazy(() => import("./ProductDetailModal"));

interface ProductCardProps {
  product: ProductCardType;
  layout?: "compact" | "full";
}

const CATEGORY_ICONS: Record<string, string> = {
  bat: "\u{1F3CF}",
  ball: "\u{26BE}",
  gloves: "\u{1F9E4}",
  pads: "\u{1F9B5}",
  helmet: "\u{26D1}",
  shoes: "\u{1F45F}",
  kit_bag: "\u{1F392}",
};

const FALLBACK_GRADIENT: Record<string, string> = {
  bat: "from-amber-900/40 to-amber-800/20",
  ball: "from-red-900/40 to-red-800/20",
  gloves: "from-blue-900/40 to-blue-800/20",
  pads: "from-green-900/40 to-green-800/20",
  helmet: "from-purple-900/40 to-purple-800/20",
  shoes: "from-cyan-900/40 to-cyan-800/20",
  kit_bag: "from-orange-900/40 to-orange-800/20",
};

function StarRating({ rating, count }: { rating: number; count?: number }) {
  const fullStars = Math.floor(rating);
  const hasHalf = rating - fullStars >= 0.3;
  return (
    <div className="flex items-center gap-1">
      <div className="flex">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-3.5 h-3.5 ${
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
        <span className="text-[11px] text-white/50">({count})</span>
      )}
    </div>
  );
}

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  layout = "full",
}) => {
  const { addToCart, sendMessage } = useChatContext();
  const [imgError, setImgError] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const handleAddToCart = () => {
    addToCart(product.id);
    sendMessage(`Add ${product.name} to cart`);
  };

  const handleLearnMore = () => {
    setShowDetailModal(true);
  };

  const category = product.category || "bat";
  const icon = CATEGORY_ICONS[category] || "\u{1F3CF}";
  const gradient =
    FALLBACK_GRADIENT[category] || "from-gray-900/40 to-gray-800/20";

  const discount =
    product.original_price && product.original_price > product.price
      ? Math.round(
          ((product.original_price - product.price) / product.original_price) *
            100,
        )
      : null;

  const hasMultipleImages = product.images && product.images.length > 1;

  if (layout === "compact") {
    return (
      <div className="bg-[#222] border border-white/10 rounded-lg p-2.5 hover:border-white/20 transition-all min-w-[160px] max-w-[180px] flex-shrink-0">
        <div
          className={`relative w-full aspect-square rounded-md overflow-hidden bg-gradient-to-br ${gradient} mb-2`}
        >
          {product.image_url && !imgError ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
              loading="lazy"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-4xl opacity-60">
              {icon}
            </div>
          )}
          {discount && (
            <span className="absolute top-1.5 right-1.5 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
              -{discount}%
            </span>
          )}
        </div>
        <h4 className="font-semibold text-xs text-white truncate">
          {product.name}
        </h4>
        <p className="text-sm font-bold text-white mt-0.5">
          NPR {product.price.toLocaleString()}
        </p>
        {product.rating !== undefined && <StarRating rating={product.rating} />}
      </div>
    );
  }

  const benefitCopy = (() => {
    const specs = product.specifications;
    if (!specs) return product.reason;
    const suitableFor = specs.suitable_for || specs.player_level;
    const batType = specs.bat_type || specs.willow_type;
    const parts: string[] = [];
    if (suitableFor) {
      const map: Record<string, string> = {
        Beginner: "Ideal for beginners",
        Intermediate: "Ideal for power hitters",
        Professional: "Ideal for serious players",
        Pro: "Ideal for serious players",
      };
      parts.push(map[suitableFor] || `Ideal for ${suitableFor}`);
    }
    if (batType && product.category === "bat") {
      parts.push(batType.includes("English") ? "Premium English Willow" : "Quality Kashmir Willow");
    }
    if (parts.length > 0) return parts.join(" · ");
    return product.reason;
  })();

  const showVerifiedBadge = (product.review_count ?? 0) >= 10;

  return (
    <>
      <div className="bg-[#222] border border-white/10 rounded-xl overflow-hidden hover:border-white/25 group-hover:shadow-[0_0_20px_rgba(245,158,11,0.2)] transition-all duration-300 group w-[220px] flex-shrink-0">
        {/* Product Image(s) */}
        <div
          className={`relative w-full aspect-[4/3] overflow-hidden bg-gradient-to-br ${gradient}`}
        >
          {hasMultipleImages ? (
            <Swiper
              modules={[Pagination]}
              pagination={{ clickable: true }}
              className="w-full h-full product-swiper"
              spaceBetween={0}
              slidesPerView={1}
            >
              {product.images!.map((imgSrc, idx) => (
                <SwiperSlide key={idx}>
                  <img
                    src={imgSrc}
                    alt={`${product.name} - angle ${idx + 1}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                </SwiperSlide>
              ))}
            </Swiper>
          ) : product.image_url && !imgError ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-6xl opacity-50">{icon}</span>
            </div>
          )}

          {discount && (
            <span className="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-md shadow-lg z-10">
              -{discount}%
            </span>
          )}

          {product.is_premium && (
            <span className="absolute top-2 left-2 bg-amber-500/90 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-md shadow-lg z-10">
              PREMIUM
            </span>
          )}

          {!product.in_stock && (
            <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-10">
              <span className="text-white/90 text-sm font-semibold bg-black/60 px-3 py-1 rounded">
                Out of Stock
              </span>
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="p-3">
          <div className="flex items-start justify-between gap-1">
            <h4 className="font-bold text-base text-white leading-tight line-clamp-2">
              {product.name}
            </h4>
          </div>

          {/* Price - prominent, with 30-day guarantee badge */}
          <div className="mt-2 flex flex-wrap items-baseline gap-2">
            <span className="text-xl font-bold text-white tracking-tight">
              NPR {product.price.toLocaleString()}
            </span>
            {product.original_price &&
              product.original_price > product.price && (
                <span className="text-xs text-white/40 line-through">
                  NPR {product.original_price.toLocaleString()}
                </span>
              )}
            <span className="text-[10px] text-amber-400/90 font-medium px-1.5 py-0.5 rounded-full border border-amber-400/40 bg-amber-400/10">
              30-Day Game-Ready
            </span>
          </div>

          {benefitCopy && (
            <p className="text-xs text-white/55 mt-1.5 line-clamp-2 leading-relaxed">
              {benefitCopy}
            </p>
          )}

          {/* Audio player for premium bats */}
          {product.audio_url && product.is_premium && (
            <div className="mt-2">
              <AudioPlayer src={product.audio_url} label="Bat Ping" />
            </div>
          )}

          {/* Stock indicator */}
          {product.in_stock && (
            <div className="mt-2">
              <span className="text-[11px] text-amber-400/90 font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full inline-block"></span>
                In Stock
              </span>
            </div>
          )}

          {/* Trust: star rating + Verified Player badge - right above actions */}
          <div className="mt-3 flex items-center justify-between gap-2 flex-wrap">
            {product.rating !== undefined && (
              <StarRating
                rating={product.rating}
                count={product.review_count}
              />
            )}
            {showVerifiedBadge && (
              <span className="text-[10px] text-amber-400 font-medium flex items-center gap-0.5">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Verified
              </span>
            )}
          </div>

          {/* Actions - gold accent for primary CTA, cohesive palette */}
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleAddToCart}
              disabled={!product.in_stock}
              className="flex-1 bg-white hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed text-[#1A1A1A] text-xs py-2 px-2 rounded-lg font-semibold transition-colors min-h-[44px]"
            >
              Add to Cart
            </button>
            <button
              onClick={() => setShowBuyModal(true)}
              disabled={!product.in_stock}
              className="bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-[#1A1A1A] text-xs py-2 px-2 rounded-lg font-semibold transition-colors min-h-[44px] min-w-[44px]"
            >
              Buy Now
            </button>
            <button
              onClick={handleLearnMore}
              className="bg-transparent hover:bg-white/10 border border-white/20 text-white text-xs py-2 px-2 rounded-lg transition-colors min-h-[44px] min-w-[44px]"
            >
              Details
            </button>
          </div>
        </div>
      </div>

      {/* Instant Buy Modal */}
      {showBuyModal && (
        <Suspense fallback={null}>
          <InstantBuyModal
            product={product}
            onClose={() => setShowBuyModal(false)}
          />
        </Suspense>
      )}

      {/* Product Detail Modal - sticky Add to Cart / Buy Now */}
      {showDetailModal && (
        <Suspense fallback={null}>
          <ProductDetailModal
            product={product}
            onClose={() => setShowDetailModal(false)}
          />
        </Suspense>
      )}
    </>
  );
};

export default ProductCard;

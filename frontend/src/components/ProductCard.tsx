import React, { useState, lazy, Suspense } from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Pagination } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/pagination';
import { ProductCard as ProductCardType } from '../types';
import { useChatContext } from '../contexts/ChatContext';
import AudioPlayer from './AudioPlayer';

const InstantBuyModal = lazy(() => import('./InstantBuyModal'));

interface ProductCardProps {
  product: ProductCardType;
  layout?: 'compact' | 'full';
}

const CATEGORY_ICONS: Record<string, string> = {
  bat: '\u{1F3CF}',
  ball: '\u{26BE}',
  gloves: '\u{1F9E4}',
  pads: '\u{1F9B5}',
  helmet: '\u{26D1}',
  shoes: '\u{1F45F}',
  kit_bag: '\u{1F392}',
};

const FALLBACK_GRADIENT: Record<string, string> = {
  bat: 'from-amber-900/40 to-amber-800/20',
  ball: 'from-red-900/40 to-red-800/20',
  gloves: 'from-blue-900/40 to-blue-800/20',
  pads: 'from-green-900/40 to-green-800/20',
  helmet: 'from-purple-900/40 to-purple-800/20',
  shoes: 'from-cyan-900/40 to-cyan-800/20',
  kit_bag: 'from-orange-900/40 to-orange-800/20',
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
                ? 'text-amber-400'
                : star === fullStars + 1 && hasHalf
                  ? 'text-amber-400/50'
                  : 'text-white/20'
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

const ProductCard: React.FC<ProductCardProps> = ({ product, layout = 'full' }) => {
  const { addToCart, sendMessage } = useChatContext();
  const [imgError, setImgError] = useState(false);
  const [showBuyModal, setShowBuyModal] = useState(false);

  const handleAddToCart = () => {
    addToCart(product.id);
    sendMessage(`Add ${product.name} to cart`);
  };

  const handleLearnMore = () => {
    sendMessage(`Tell me more about ${product.name}`);
  };

  const category = product.category || 'bat';
  const icon = CATEGORY_ICONS[category] || '\u{1F3CF}';
  const gradient = FALLBACK_GRADIENT[category] || 'from-gray-900/40 to-gray-800/20';

  const discount = product.original_price && product.original_price > product.price
    ? Math.round(((product.original_price - product.price) / product.original_price) * 100)
    : null;

  const hasMultipleImages = product.images && product.images.length > 1;

  if (layout === 'compact') {
    return (
      <div className="bg-[#222] border border-white/10 rounded-lg p-2.5 hover:border-white/20 transition-all min-w-[160px] max-w-[180px] flex-shrink-0">
        <div className={`relative w-full aspect-square rounded-md overflow-hidden bg-gradient-to-br ${gradient} mb-2`}>
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
        <h4 className="font-semibold text-xs text-white truncate">{product.name}</h4>
        <p className="text-sm font-bold text-white mt-0.5">NPR {product.price.toLocaleString()}</p>
        {product.rating !== undefined && (
          <StarRating rating={product.rating} />
        )}
      </div>
    );
  }

  return (
    <>
      <div className="bg-[#222] border border-white/10 rounded-xl overflow-hidden hover:border-white/25 transition-all group w-[220px] flex-shrink-0">
        {/* Product Image(s) */}
        <div className={`relative w-full aspect-[4/3] overflow-hidden bg-gradient-to-br ${gradient}`}>
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
              <span className="text-white/90 text-sm font-semibold bg-black/60 px-3 py-1 rounded">Out of Stock</span>
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="p-3">
          <div className="flex items-start justify-between gap-1">
            <h4 className="font-semibold text-sm text-white leading-tight line-clamp-2">
              {product.name}
            </h4>
          </div>

          {product.rating !== undefined && (
            <div className="mt-1.5">
              <StarRating rating={product.rating} count={product.review_count} />
            </div>
          )}

          {/* Price */}
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-lg font-bold text-white">
              NPR {product.price.toLocaleString()}
            </span>
            {product.original_price && product.original_price > product.price && (
              <span className="text-xs text-white/40 line-through">
                NPR {product.original_price.toLocaleString()}
              </span>
            )}
          </div>

          {product.reason && (
            <p className="text-xs text-white/60 mt-1.5 line-clamp-2 leading-relaxed">
              {product.reason}
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
              <span className="text-[11px] text-emerald-400 font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full inline-block"></span>
                In Stock
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleAddToCart}
              disabled={!product.in_stock}
              className="flex-1 bg-white hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed text-[#1A1A1A] text-xs py-2 px-2 rounded-lg font-semibold transition-colors"
            >
              Add to Cart
            </button>
            <button
              onClick={() => setShowBuyModal(true)}
              disabled={!product.in_stock}
              className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs py-2 px-2 rounded-lg font-semibold transition-colors"
            >
              Buy Now
            </button>
            <button
              onClick={handleLearnMore}
              className="bg-transparent hover:bg-white/10 border border-white/20 text-white text-xs py-2 px-2 rounded-lg transition-colors"
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
    </>
  );
};

export default ProductCard;

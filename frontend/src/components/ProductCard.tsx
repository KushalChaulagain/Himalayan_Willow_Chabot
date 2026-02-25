import React from 'react';
import { ProductCard as ProductCardType } from '../types';
import { useChatContext } from '../contexts/ChatContext';

interface ProductCardProps {
  product: ProductCardType;
}

const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const { addToCart, sendMessage } = useChatContext();

  const handleAddToCart = () => {
    addToCart(product.id);
    sendMessage(`Add ${product.name} to cart`);
  };

  const handleLearnMore = () => {
    sendMessage(`Tell me more about ${product.name}`);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex space-x-3">
        {/* Product Image */}
        {product.image_url && (
          <div className="w-20 h-20 flex-shrink-0">
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover rounded"
              loading="lazy"
            />
          </div>
        )}

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-sm text-gray-900 truncate">
            {product.name}
          </h4>
          <p className="text-lg font-bold text-primary-600 mt-1">
            NPR {product.price.toLocaleString()}
          </p>
          <p className="text-xs text-gray-600 mt-1 line-clamp-2">
            {product.reason}
          </p>

          {/* Stock Status */}
          <div className="mt-2">
            {product.in_stock ? (
              <span className="text-xs text-green-600 font-medium">In Stock</span>
            ) : (
              <span className="text-xs text-red-600 font-medium">Out of Stock</span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex space-x-2 mt-3">
        <button
          onClick={handleAddToCart}
          disabled={!product.in_stock}
          className="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm py-2 px-3 rounded transition-colors"
        >
          Add to Cart
        </button>
        <button
          onClick={handleLearnMore}
          className="flex-1 bg-white hover:bg-gray-50 border border-gray-300 text-gray-700 text-sm py-2 px-3 rounded transition-colors"
        >
          Learn More
        </button>
      </div>
    </div>
  );
};

export default ProductCard;

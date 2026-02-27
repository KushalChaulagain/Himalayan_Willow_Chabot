import React, { useEffect, useMemo, useState } from "react";
import { useChatContext } from "../contexts/ChatContext";

interface CartSummaryBarProps {
  onOpenCart: () => void;
}

const CartSummaryBar: React.FC<CartSummaryBarProps> = ({ onOpenCart }) => {
  const { apiClient, cartItems } = useChatContext();
  const [cartProducts, setCartProducts] = useState<
    Array<{ id: number; name: string; price: number }>
  >([]);
  const [loading, setLoading] = useState(false);

  const cartTotal = useMemo(() => {
    const idToPrice: Record<number, number> = {};
    cartProducts.forEach((p) => {
      idToPrice[p.id] = p.price;
    });
    return cartItems.reduce(
      (sum, id) => sum + (idToPrice[id] ?? 0),
      0
    );
  }, [cartItems, cartProducts]);

  useEffect(() => {
    if (cartItems.length === 0) {
      setCartProducts([]);
      return;
    }
    setLoading(true);
    apiClient
      .getCartProducts(cartItems)
      .then((products) =>
        setCartProducts(
          products.map((p) => ({
            id: p.id,
            name: p.name,
            price: p.price,
          }))
        )
      )
      .finally(() => setLoading(false));
  }, [cartItems, apiClient]);

  const itemLabel =
    cartItems.length === 1 ? "1 item in cart" : `${cartItems.length} items in cart`;

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 bg-[#262626] border-t border-white/10 shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-sm text-white/80 font-medium truncate">
          {itemLabel}
        </span>
        <span className="text-sm text-white/60 shrink-0">
          {loading ? (
            "Loading..."
          ) : (
            <>NPR {cartTotal.toLocaleString()}</>
          )}
        </span>
      </div>
      <button
        onClick={onOpenCart}
        className="shrink-0 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-[#1A1A1A] text-sm font-semibold transition-colors"
      >
        View Cart
      </button>
    </div>
  );
};

export default CartSummaryBar;

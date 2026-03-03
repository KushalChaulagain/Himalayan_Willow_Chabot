import { AnimatePresence, motion } from "framer-motion";
import React, { useEffect, useState } from "react";
import { useChatContext } from "../contexts/ChatContext";
import { loadProfile } from "../utils/userProfile";

interface PurchaseItem {
  product_name: string;
  price: number;
  image_url?: string;
  category?: string;
  date: string;
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

const KitBagView: React.FC<{ open: boolean; onClose: () => void }> = ({
  open,
  onClose,
}) => {
  const { apiClient, sessionId, cartItems, removeFromCartAt } =
    useChatContext();
  const [purchases, setPurchases] = useState<PurchaseItem[]>([]);
  const [cartProducts, setCartProducts] = useState<
    Array<{
      id: number;
      name: string;
      price: number;
      image_url?: string;
      category?: string;
    }>
  >([]);
  const [cartProductsLoading, setCartProductsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [profileInfo, setProfileInfo] = useState<Record<string, string>>({});

  const idToProduct = React.useMemo(() => {
    const map: Record<
      number,
      {
        id: number;
        name: string;
        price: number;
        image_url?: string;
        category?: string;
      }
    > = {};
    cartProducts.forEach((p) => {
      map[p.id] = p;
    });
    return map;
  }, [cartProducts]);

  const cartTotal = React.useMemo(() => {
    return cartItems.reduce(
      (sum, id) => sum + (idToProduct[id]?.price ?? 0),
      0,
    );
  }, [cartItems, idToProduct]);

  useEffect(() => {
    if (!open) return;

    const profile = loadProfile();
    if (profile) {
      const info: Record<string, string> = {};
      if (profile.playing_level) info["Level"] = profile.playing_level;
      if (profile.preferred_surface)
        info["Surface"] = profile.preferred_surface;
      if (profile.city) info["City"] = profile.city;
      setProfileInfo(info);
    }

    if (sessionId) {
      setLoading(true);
      apiClient
        .getUserProfile(sessionId)
        .then((data) => {
          if (data?.purchase_history) {
            setPurchases(
              (data.purchase_history as unknown as PurchaseItem[]).map(
                (item) => ({
                  product_name:
                    item.product_name || (item as any).name || "Unknown",
                  price: item.price ?? 0,
                  image_url: item.image_url,
                  category: item.category,
                  date: item.date,
                }),
              ),
            );
          }
        })
        .finally(() => setLoading(false));
    }
  }, [open, sessionId, apiClient]);

  useEffect(() => {
    if (!open || cartItems.length === 0) {
      setCartProducts([]);
      return;
    }
    setCartProductsLoading(true);
    apiClient
      .getCartProducts(cartItems)
      .then((products) => {
        setCartProducts(
          products.map((p) => ({
            id: p.id,
            name: p.name,
            price: p.price,
            image_url: p.image_url,
            category: p.category,
          })),
        );
      })
      .finally(() => setCartProductsLoading(false));
  }, [open, cartItems, apiClient]);

  const daysSincePurchase = (dateStr: string): number => {
    return Math.floor(
      (Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24),
    );
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40 z-20"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="absolute right-0 top-0 bottom-0 w-[min(100%,18rem)] sm:w-72 bg-[#1A1A1A] border-l border-white/10 z-30 overflow-y-auto shadow-premium-lg"
          >
            <div className="p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-sm flex items-center gap-2">
                  <span>{"\u{1F392}"}</span> My Kit Bag
                </h3>
                <button
                  onClick={onClose}
                  className="text-white/50 hover:text-white p-1"
                >
                  <svg
                    className="w-4 h-4"
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

              {/* Profile summary */}
              {Object.keys(profileInfo).length > 0 && (
                <div className="bg-white/5 border border-white/10 rounded-xl p-3 mb-4 shadow-premium-sm">
                  <p className="text-[10px] text-white/40 uppercase tracking-wider mb-2 font-medium">
                    Your Profile
                  </p>
                  {Object.entries(profileInfo).map(([key, val]) => (
                    <div
                      key={key}
                      className="flex justify-between text-xs mb-1"
                    >
                      <span className="text-white/50">{key}</span>
                      <span className="text-white capitalize">{val}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Cart items */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-3 mb-4 shadow-premium-sm">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-white/60">Items in Cart</span>
                  <span className="text-sm font-bold text-white">
                    {cartItems.length}
                  </span>
                </div>
                {cartProductsLoading && cartItems.length > 0 && (
                  <div className="text-xs text-white/40 py-2">
                    Loading cart...
                  </div>
                )}
                {!cartProductsLoading && cartItems.length > 0 && (
                  <div className="space-y-2 mt-2">
                    {cartItems.map((productId, index) => {
                      const item = idToProduct[productId];
                      const icon = item
                        ? CATEGORY_ICONS[item.category || "bat"] || "\u{1F3CF}"
                        : "\u{1F3CF}";
                      return (
                        <div
                          key={`${productId}-${index}`}
                          className="flex gap-2 items-center bg-white/5 rounded p-2"
                        >
                          <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-lg flex-shrink-0">
                            {item?.image_url ? (
                              <img
                                src={item.image_url}
                                alt=""
                                className="w-full h-full object-cover rounded"
                              />
                            ) : (
                              icon
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-white font-medium truncate">
                              {item?.name ?? `Product #${productId}`}
                            </p>
                            <p className="text-[10px] text-white/40">
                              NPR {item?.price?.toLocaleString() ?? "—"}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeFromCartAt(index)}
                            className="flex-shrink-0 p-1.5 rounded text-white/50 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                            aria-label="Remove from cart"
                            title="Remove from cart"
                          >
                            <svg
                              className="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                              />
                            </svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
                {!cartProductsLoading && cartItems.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-white/10 flex justify-between items-center">
                    <span className="text-xs text-white/60">Subtotal</span>
                    <span className="text-sm font-bold text-white">
                      NPR {cartTotal.toLocaleString()}
                    </span>
                  </div>
                )}
                {!cartProductsLoading &&
                  cartItems.length > 0 &&
                  cartProducts.length === 0 && (
                    <p className="text-xs text-white/40 mt-2">
                      Cart items could not be loaded.
                    </p>
                  )}
              </div>

              {/* Purchase history */}
              <div>
                <p className="text-[10px] text-white/40 uppercase tracking-wider mb-2 font-medium">
                  Past Purchases
                </p>

                {loading && (
                  <div className="text-xs text-white/40 py-4 text-center">
                    Loading...
                  </div>
                )}

                {!loading && purchases.length === 0 && (
                  <div className="text-xs text-white/40 py-4 text-center">
                    No purchases yet. Find your first gear!
                  </div>
                )}

                <div className="space-y-2">
                  {purchases.map((item, idx) => {
                    const days = daysSincePurchase(item.date);
                    const needsReGrip = item.category === "bat" && days > 90;
                    const icon =
                      CATEGORY_ICONS[item.category || "bat"] || "\u{1F3CF}";

                    return (
                      <div
                        key={idx}
                        className="bg-white/5 border border-white/10 rounded-xl p-2.5 shadow-premium-sm"
                      >
                        <div className="flex gap-2 items-start">
                          <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-lg flex-shrink-0">
                            {item.image_url ? (
                              <img
                                src={item.image_url}
                                alt=""
                                className="w-full h-full object-cover rounded"
                              />
                            ) : (
                              icon
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-white font-medium truncate">
                              {item.product_name}
                            </p>
                            <p className="text-[10px] text-white/40">
                              {days} days ago &middot; NPR{" "}
                              {item.price?.toLocaleString()}
                            </p>
                          </div>
                        </div>
                        {needsReGrip && (
                          <div className="mt-1.5 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-1">
                            <p className="text-[10px] text-amber-400">
                              Time to re-grip your bat? Fresh grips improve
                              control!
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default KitBagView;

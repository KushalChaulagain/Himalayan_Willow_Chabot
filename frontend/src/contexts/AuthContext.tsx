import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

const TOKEN_KEY = 'hw_auth_token';
const USER_KEY = 'hw_auth_user';

export interface AuthUser {
  id: number;
  email?: string;
  name?: string;
  avatar_url?: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
  setAuthFromCredential: (credential: string, apiUrl: string) => Promise<boolean>;
  linkSession: (sessionId: string, apiUrl: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

function loadStoredAuth(): AuthState {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);
    if (token && userStr) {
      const user = JSON.parse(userStr) as AuthUser;
      return { token, user, isLoading: false };
    }
  } catch {
    // ignore
  }
  return { token: null, user: null, isLoading: false };
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(() => {
    const stored = loadStoredAuth();
    return { ...stored, isLoading: true };
  });

  useEffect(() => {
    const stored = loadStoredAuth();
    setState((prev) => ({ ...prev, ...stored, isLoading: false }));
  }, []);

  const login = useCallback((token: string, user: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    setState({ token, user, isLoading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setState({ token: null, user: null, isLoading: false });
  }, []);

  const setAuthFromCredential = useCallback(async (credential: string, apiUrl: string): Promise<boolean> => {
    try {
      const base = apiUrl.replace(/\/$/, '');
      const res = await fetch(`${base}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (data.token && data.user) {
        login(data.token, {
          id: data.user.id,
          email: data.user.email,
          name: data.user.name,
          avatar_url: data.user.avatar_url,
        });
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, [login]);

  const linkSession = useCallback(async (sessionId: string, apiUrl: string) => {
    if (!state.token) return;
    try {
      const base = apiUrl.replace(/\/$/, '');
      await fetch(`${base}/api/auth/link-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${state.token}`,
        },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch {
      // ignore - session will be linked on next message
    }
  }, [state.token]);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        setAuthFromCredential,
        linkSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

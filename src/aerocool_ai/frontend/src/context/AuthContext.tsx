import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '../types';
import { demoLogin, fetchMyProfile, loginUser, registerUser } from '../services/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAdmin: boolean;
  isCustomer: boolean;
  isAuthenticated: boolean;
  isLoginModalOpen: boolean;
  openLoginModal: () => void;
  closeLoginModal: () => void;
  login: (email: string, pass: string) => Promise<void>;
  register: (email: string, pass: string, name: string, role: UserRole, org?: string) => Promise<void>;
  quickSwitchRole: (role: 'admin' | 'customer') => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('aerocool_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('aerocool_token'));
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  useEffect(() => {
    if (token) {
      fetchMyProfile(token)
        .then((profile) => {
          setUser(profile);
          localStorage.setItem('aerocool_user', JSON.stringify(profile));
        })
        .catch((err) => {
          console.error('Profile fetch failed:', err);
          logout();
        });
    }
  }, [token]);

  const saveAuthSession = (newToken: string, newUser: UserProfile) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('aerocool_token', newToken);
    localStorage.setItem('aerocool_user', JSON.stringify(newUser));
  };

  const login = async (email: string, pass: string) => {
    const data = await loginUser(email, pass);
    saveAuthSession(data.access_token, data.user);
    setIsLoginModalOpen(false);
  };

  const register = async (email: string, pass: string, name: string, role: UserRole, org?: string) => {
    const data = await registerUser(email, pass, name, role, org);
    saveAuthSession(data.access_token, data.user);
    setIsLoginModalOpen(false);
  };

  const quickSwitchRole = async (role: 'admin' | 'customer') => {
    const data = await demoLogin(role);
    saveAuthSession(data.access_token, data.user);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('aerocool_token');
    localStorage.removeItem('aerocool_user');
  };

  const openLoginModal = () => setIsLoginModalOpen(true);
  const closeLoginModal = () => setIsLoginModalOpen(false);

  const isAdmin = user?.role === 'admin';
  const isCustomer = user?.role === 'customer';
  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAdmin,
        isCustomer,
        isAuthenticated,
        isLoginModalOpen,
        openLoginModal,
        closeLoginModal,
        login,
        register,
        quickSwitchRole,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

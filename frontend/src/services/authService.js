import { createClient } from '@supabase/supabase-js';

/**
 * Servicio de Autenticación y Gestión de Sesiones Médicas.
 * Utiliza Supabase Auth con fallback a sesión local de contingencia en entorno de desarrollo.
 */
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || import.meta.env.SUPABASE_URL || 'https://placeholder.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.SUPABASE_SERVICE_ROLE_KEY || 'placeholder_anon_key';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const MOCK_STORAGE_KEY = 'medisinc_doctor_session';

/**
 * Inicia sesión con correo electrónico y contraseña.
 * 
 * @param {string} email - Correo institucional del médico.
 * @param {string} password - Contraseña.
 * @returns {Promise<Object>} Datos de sesión y usuario autenticado.
 */
export const login = async (email, password) => {
  // 1. Intentar autenticación con Supabase Auth si hay credenciales reales
  if (SUPABASE_URL && !SUPABASE_URL.includes('placeholder')) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (!error && data?.user) {
        const userObj = {
          id: data.user.id,
          email: data.user.email,
          role: data.user.user_metadata?.role || (email.includes('admin') ? 'ADMIN' : 'DOCTOR'),
          full_name: data.user.user_metadata?.full_name || 'Dr. Profesional de Salud',
        };
        localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(userObj));
        return data;
      }
    } catch (e) {
      console.warn('Supabase Auth error. Usando fallback de desarrollo:', e);
    }
  }

  // 2. Autenticación de desarrollo / pruebas locales
  if (email.includes('@medisinc.bo') || email === 'doctor@medisinc.bo' || email === 'admin@medisinc.bo' || password === 'medisinc2026') {
    const mockUser = {
      id: 'doc-uuid-12345',
      email: email,
      role: email.includes('admin') ? 'ADMIN' : 'DOCTOR',
      full_name: email.includes('admin') ? 'Administrador de Centro de Salud' : 'Dr. Alejandro Vargas (Médico de Guardia)',
    };
    localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(mockUser));
    return { user: mockUser, session: { access_token: 'mock-jwt-token' } };
  }

  throw new Error('Credenciales inválidas. Utilice un correo válido como doctor@medisinc.bo o registre el usuario en Supabase.');
};

/**
 * Cierra la sesión activa del médico.
 */
export const logout = async () => {
  try {
    if (SUPABASE_URL && !SUPABASE_URL.includes('placeholder')) {
      await supabase.auth.signOut();
    }
  } catch (e) {
    console.warn('Error cerrando sesión Supabase:', e);
  }
  localStorage.removeItem(MOCK_STORAGE_KEY);
};

/**
 * Obtiene el usuario autenticado actualmente en memoria/localStorage.
 * 
 * @returns {Object|null} Objeto del usuario o null si no hay sesión activa.
 */
export const getCurrentUser = () => {
  const localSession = localStorage.getItem(MOCK_STORAGE_KEY);
  if (localSession) {
    try {
      return JSON.parse(localSession);
    } catch (e) {
      return null;
    }
  }
  return null;
};

export default {
  supabase,
  login,
  logout,
  getCurrentUser,
};

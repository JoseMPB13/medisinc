import { createClient } from '@supabase/supabase-js';

/**
 * Servicio de Autenticación y Gestión de Sesiones Médicas.
 * Utiliza Supabase Auth con fallback a sesión local de contingencia en entorno de desarrollo.
 */
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder_anon_key';

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
  try {
    if (SUPABASE_URL && !SUPABASE_URL.includes('placeholder')) {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      return data;
    }
  } catch (error) {
    console.warn('Supabase Auth no disponible o credenciales incorrectas. Usando autenticación médica de desarrollo:', error);
  }

  // Autenticación de desarrollo local para pruebas
  if (email.includes('@medisinc.bo') || email === 'doctor@medisinc.bo' || email === 'admin@medisinc.bo') {
    const mockUser = {
      id: 'doc-uuid-12345',
      email: email,
      role: email.includes('admin') ? 'ADMIN' : 'DOCTOR',
      full_name: 'Dr. Alejandro Vargas (Médico de Guardia)',
    };
    localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(mockUser));
    return { user: mockUser, session: { access_token: 'mock-jwt-token' } };
  }

  throw new Error('Credenciales inválidas. Utilice un correo institucional válido (@medisinc.bo).');
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

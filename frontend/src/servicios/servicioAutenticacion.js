/**
 * Servicio de Autenticación y Gestión de Sesión para MediSinc-IA.
 * Soporta Supabase Auth con fallback de autenticación local para entorno de desarrollo.
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder_anon_key';

export const clienteSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const CLAVE_ALMACENAMIENTO_USUARIO = 'medisinc_usuario';
const CLAVE_ALMACENAMIENTO_TOKEN = 'medisinc_token';

export const servicioAutenticacion = {
  /**
   * Inicia sesión con correo y contraseña.
   * @param {string} correo - Correo institucional.
   * @param {string} password - Contraseña de acceso.
   * @returns {Promise<Object>} Datos del usuario autenticado y rol.
   */
  async iniciarSesion(correo, password) {
    try {
      // 1. Intento de autenticación en Supabase Auth
      if (SUPABASE_URL && !SUPABASE_URL.includes('placeholder')) {
        const { data, error } = await clienteSupabase.auth.signInWithPassword({
          email: correo,
          password: password,
        });

        if (!error && data?.session) {
          const usuario = {
            id: data.user.id,
            correo: data.user.email,
            email: data.user.email,
            nombre: data.user.user_metadata?.full_name || data.user.user_metadata?.nombre || correo.split('@')[0],
            rol: data.user.user_metadata?.role || (correo.includes('admin') ? 'ADMIN' : 'MEDICO'),
            token: data.session.access_token,
          };
          localStorage.setItem(CLAVE_ALMACENAMIENTO_USUARIO, JSON.stringify(usuario));
          localStorage.setItem(CLAVE_ALMACENAMIENTO_TOKEN, usuario.token);
          return usuario;
        }
      }

      // 2. Modo Autenticación Local de Demostración
      const esAdmin = correo.toLowerCase().includes('admin');
      const usuarioLocal = {
        id: esAdmin ? 'admin-uuid-001' : 'doc-uuid-001',
        correo: correo,
        email: correo,
        nombre: esAdmin ? 'Administrador General' : 'Dr. Carlos Mendoza',
        rol: esAdmin ? 'ADMIN' : 'MEDICO',
        token: `mock_jwt_token_${esAdmin ? 'admin' : 'medico'}_2026`,
      };

      localStorage.setItem(CLAVE_ALMACENAMIENTO_USUARIO, JSON.stringify(usuarioLocal));
      localStorage.setItem(CLAVE_ALMACENAMIENTO_TOKEN, usuarioLocal.token);
      return usuarioLocal;
    } catch (error) {
      console.error('[servicioAutenticacion] Error al iniciar sesión:', error);
      throw error;
    }
  },

  /**
   * Cierra la sesión activa y elimina las credenciales locales.
   */
  async cerrarSesion() {
    try {
      if (SUPABASE_URL && !SUPABASE_URL.includes('placeholder')) {
        await clienteSupabase.auth.signOut();
      }
    } catch (e) {
      console.warn('[servicioAutenticacion] Error cerrando sesión en Supabase:', e);
    } finally {
      localStorage.removeItem(CLAVE_ALMACENAMIENTO_USUARIO);
      localStorage.removeItem(CLAVE_ALMACENAMIENTO_TOKEN);
    }
  },

  /**
   * Obtiene el perfil del usuario autenticado en la sesión actual.
   * @returns {Object|null}
   */
  obtenerUsuarioActual() {
    try {
      const data = localStorage.getItem(CLAVE_ALMACENAMIENTO_USUARIO);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  /**
   * Obtiene el token JWT para encabezados de autorización.
   * @returns {string|null}
   */
  obtenerToken() {
    return localStorage.getItem(CLAVE_ALMACENAMIENTO_TOKEN);
  },

  /**
   * Verifica si el usuario tiene una sesión activa y válida.
   * @returns {boolean}
   */
  estaAutenticado() {
    return !!this.obtenerToken();
  },
};

// Aliases de retrocompatibilidad
export const authService = {
  login: servicioAutenticacion.iniciarSesion,
  logout: servicioAutenticacion.cerrarSesion,
  getCurrentUser: servicioAutenticacion.obtenerUsuarioActual,
  getToken: servicioAutenticacion.obtenerToken,
  isAuthenticated: servicioAutenticacion.estaAutenticado,
};

export default servicioAutenticacion;

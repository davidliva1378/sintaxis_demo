export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  has_pjn_credentials: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface PJNCredentials {
  pjn_usuario_encrypted: string
  pjn_password_encrypted: string
}

export interface PJNCredentialsResponse {
  has_credentials: boolean
  pjn_usuario_encrypted: string | null
  pjn_password_encrypted: string | null
}

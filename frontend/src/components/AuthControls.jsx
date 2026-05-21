import React from 'react';
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';

const googleClientId =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ||
  (import.meta.env.MODE === 'test' ? 'test-google-client-id' : '');

export default function AuthControls({
  user,
  loading,
  onLogin,
  onLogout,
  onError,
  onNavigateProfile,
}) {
  if (user) {
    return (
      <details className="auth-controls auth-controls-signed-in auth-menu">
        <summary className="auth-menu-trigger">
          {user.avatar_url ? (
            <img className="auth-avatar" src={user.avatar_url} alt={`${user.name} avatar`} />
          ) : null}
          <div className="auth-user-meta">
            <span className="auth-user-name">{user.name}</span>
            <span className="auth-user-email">{user.email}</span>
          </div>
          <span className="auth-menu-caret" aria-hidden="true">
            ▾
          </span>
        </summary>
        <div className="auth-menu-dropdown">
          <button type="button" className="ghost auth-menu-item" onClick={onNavigateProfile}>
            Profile
          </button>
          <button
            type="button"
            className="ghost auth-menu-item"
            onClick={onLogout}
            disabled={loading}
          >
            Log out
          </button>
        </div>
      </details>
    );
  }

  if (!googleClientId) {
    return <p className="auth-unavailable">Google login unavailable</p>;
  }

  return (
    <div className="auth-controls auth-controls-signed-out">
      <GoogleOAuthProvider clientId={googleClientId}>
        <GoogleLogin
          text="signin_with"
          shape="pill"
          onSuccess={(credentialResponse) => {
            if (!credentialResponse.credential) {
              onError?.('Google did not return a credential');
              return;
            }

            onLogin(credentialResponse.credential);
          }}
          onError={() => onError?.('Google login failed')}
        />
      </GoogleOAuthProvider>
    </div>
  );
}

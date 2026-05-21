import React from 'react';
import UserInterestsPage from './UserInterestsPage';

function getInitials(name = '', email = '') {
  const trimmedName = name.trim();
  if (trimmedName) {
    const initials = trimmedName
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || '')
      .join('');
    if (initials) return initials;
  }

  return (email[0] || '?').toUpperCase();
}

export default function ProfilePage({ currentUser, onError }) {
  return (
    <section className="profile-page reveal">
      <div className="profile-summary card">
        <p className="eyebrow">Profile</p>
        <h2>Your practice profile</h2>
        {currentUser ? (
          <div className="profile-summary-user">
            {currentUser.avatar_url ? (
              <img
                className="profile-summary-avatar"
                src={currentUser.avatar_url}
                alt={`${currentUser.name} avatar`}
              />
            ) : (
              <div className="profile-summary-avatar profile-summary-avatar-fallback">
                {getInitials(currentUser.name, currentUser.email)}
              </div>
            )}
            <div className="profile-summary-meta">
              <strong>{currentUser.name}</strong>
              <span>{currentUser.email}</span>
            </div>
          </div>
        ) : (
          <p className="muted">
            Sign in to save your interests and keep your practice preferences in one place.
          </p>
        )}
      </div>

      <UserInterestsPage currentUser={currentUser} onError={onError} />
    </section>
  );
}

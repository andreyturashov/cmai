import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { LANGUAGE_OPTIONS } from '../constants/languageOptions';

const MAX_INTERESTS = 5;

export default function UserInterestsPage({ currentUser, onError }) {
  const [selectedInterests, setSelectedInterests] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadInterests() {
      if (!currentUser) {
        setSelectedInterests([]);
        setSaved(false);
        return;
      }

      try {
        setLoading(true);
        onError('');
        const response = await api.getUserInterests();
        if (!active) return;
        setSelectedInterests(response.interests || []);
        setSaved(false);
      } catch (error) {
        if (!active) return;
        onError(error.message || 'Failed to load user interests');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadInterests();

    return () => {
      active = false;
    };
  }, [currentUser, onError]);

  const selectionLimitReached = selectedInterests.length >= MAX_INTERESTS;
  const selectedLabels = useMemo(
    () => LANGUAGE_OPTIONS.filter((option) => selectedInterests.includes(option.value)),
    [selectedInterests],
  );

  function toggleInterest(value) {
    setSaved(false);
    setSelectedInterests((previous) => {
      if (previous.includes(value)) {
        return previous.filter((interest) => interest !== value);
      }

      if (previous.length >= MAX_INTERESTS) {
        return previous;
      }

      return [...previous, value];
    });
  }

  async function saveInterests() {
    try {
      setSaving(true);
      onError('');
      const response = await api.updateUserInterests({ interests: selectedInterests });
      setSelectedInterests(response.interests || []);
      setSaved(true);
    } catch (error) {
      onError(error.message || 'Failed to save user interests');
    } finally {
      setSaving(false);
    }
  }

  if (!currentUser) {
    return (
      <section className="user-interests-empty card reveal">
        <p className="eyebrow">User Interests</p>
        <h2>Sign in to choose your learning categories</h2>
        <p className="muted">
          Save up to five categories so your learning focus is easy to revisit later.
        </p>
      </section>
    );
  }

  return (
    <section className="user-interests-panel card reveal">
      <div className="user-interests-header">
        <p className="eyebrow">User Interests</p>
        <h2>Choose up to 5 categories to learn</h2>
        <p className="muted">
          Pick the tracks you want to focus on next, such as Python theory or JavaScript.
        </p>
      </div>

      <div className="user-interests-meta">
        <span>
          Selected: {selectedInterests.length}/{MAX_INTERESTS}
        </span>
        {saved ? <span className="user-interests-saved">Saved</span> : null}
      </div>

      {loading ? <p className="muted">Loading your saved interests...</p> : null}

      <div className="user-interests-grid">
        {LANGUAGE_OPTIONS.map((option) => {
          const isSelected = selectedInterests.includes(option.value);
          const disabled = !isSelected && selectionLimitReached;
          return (
            <button
              key={option.value}
              type="button"
              className={`interest-chip${isSelected ? ' interest-chip-selected' : ''}`}
              onClick={() => toggleInterest(option.value)}
              disabled={disabled || loading || saving}
            >
              <span>{option.label}</span>
            </button>
          );
        })}
      </div>

      <div className="user-interests-selection card">
        <p className="eyebrow">Current Selection</p>
        {selectedLabels.length ? (
          <div className="user-interests-tags">
            {selectedLabels.map((option) => (
              <span key={option.value} className="user-interest-tag">
                {option.label}
              </span>
            ))}
          </div>
        ) : (
          <p className="muted">No categories selected yet.</p>
        )}
      </div>

      <div className="user-interests-actions">
        <button type="button" onClick={saveInterests} disabled={saving || loading}>
          {saving ? 'Saving...' : 'Save Interests'}
        </button>
      </div>
    </section>
  );
}

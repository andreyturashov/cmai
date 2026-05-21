import React, { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { LANGUAGE_OPTIONS } from '../constants/languageOptions';

const MAX_INTERESTS = 5;
const AUTO_SAVE_DELAY_MS = 200;

export default function UserInterestsPage({ currentUser, onError }) {
  const [selectedInterests, setSelectedInterests] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const lastSavedSelectionRef = useRef('');
  const requestIdRef = useRef(0);

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
        const nextInterests = response.interests || [];
        setSelectedInterests(nextInterests);
        lastSavedSelectionRef.current = JSON.stringify(nextInterests);
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
  const currentSelectionKey = JSON.stringify(selectedInterests);

  useEffect(() => {
    if (!currentUser || loading || currentSelectionKey === lastSavedSelectionRef.current) {
      return undefined;
    }

    const timer = window.setTimeout(async () => {
      const requestId = requestIdRef.current + 1;
      requestIdRef.current = requestId;

      try {
        setSaving(true);
        onError('');
        await api.updateUserInterests({ interests: selectedInterests });
        if (requestId !== requestIdRef.current) {
          return;
        }

        lastSavedSelectionRef.current = currentSelectionKey;
        setSaved(true);
      } catch (error) {
        if (requestId === requestIdRef.current) {
          onError(error.message || 'Failed to save user interests');
        }
      } finally {
        if (requestId === requestIdRef.current) {
          setSaving(false);
        }
      }
    }, AUTO_SAVE_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [currentSelectionKey, currentUser, loading, onError, selectedInterests]);

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
        {saving ? <span className="user-interests-saved">Saving...</span> : null}
        {!saving && saved ? <span className="user-interests-saved">Saved</span> : null}
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
              disabled={disabled || loading}
            >
              <span>{option.label}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

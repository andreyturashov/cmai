import React, { cloneElement, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityCalendar } from 'react-activity-calendar';
import 'react-activity-calendar/tooltips.css';
import { api } from '../api/client';
import LeftPanel from './LeftPanel';
import CodeReviewPanel from './CodeReviewPanel';

const CALENDAR_WEEK_START = 1;
const CALENDAR_BLOCK_MARGIN = 4;
const DEFAULT_CALENDAR_BLOCK_SIZE = 13;
const MIN_CALENDAR_BLOCK_SIZE = 10;
const MAX_CALENDAR_BLOCK_SIZE = 16;
const CALENDAR_WEEKDAY_LABEL_SPACE = 56;

function formatDayKey(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toISOString().slice(0, 10);
}

function buildCalendarData(entries, year) {
  const startDate = new Date(Date.UTC(year, 0, 1));
  const endDate = new Date(Date.UTC(year, 11, 31));
  const countsByDay = new Map(entries.map((entry) => [entry.day, entry.completed_tasks]));
  const data = [];

  for (
    const cursor = new Date(startDate);
    cursor <= endDate;
    cursor.setUTCDate(cursor.getUTCDate() + 1)
  ) {
    const day = cursor.toISOString().slice(0, 10);
    const count = countsByDay.get(day) || 0;
    let level = 0;

    if (count === 1) {
      level = 1;
    } else if (count <= 3 && count > 1) {
      level = 2;
    } else if (count <= 5 && count > 3) {
      level = 3;
    } else if (count > 5) {
      level = 4;
    }

    data.push({ date: day, count, level });
  }

  return data;
}

function getCalendarWeekCount(year, weekStart) {
  const startDate = new Date(Date.UTC(year, 0, 1));
  const endDate = new Date(Date.UTC(year, 11, 31));
  const firstWeekOffset = (startDate.getUTCDay() - weekStart + 7) % 7;
  const totalDays = Math.floor((endDate - startDate) / 86400000) + 1;

  return Math.ceil((firstWeekOffset + totalDays) / 7);
}

function formatMeta(entry) {
  const updatedAt = entry?.updated_at ? new Date(entry.updated_at) : null;
  const formattedDate =
    updatedAt && !Number.isNaN(updatedAt.getTime())
      ? new Intl.DateTimeFormat(undefined, {
          month: 'short',
          day: 'numeric',
        }).format(updatedAt)
      : 'No date';

  return `${entry.task.language} · ${entry.score}/10 · ${formattedDate}`;
}

function formatComplexity(value = '') {
  if (!value) return '';

  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export default function TaskProgressPage({ currentUser, onError }) {
  const [progressEntries, setProgressEntries] = useState([]);
  const [dailyProgress, setDailyProgress] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showReference, setShowReference] = useState(false);
  const [calendarHostWidth, setCalendarHostWidth] = useState(0);
  const calendarHostRef = useRef(null);
  const calendarYear = useMemo(() => new Date().getFullYear(), []);

  useEffect(() => {
    let active = true;

    async function loadProgress() {
      if (!currentUser) {
        setProgressEntries([]);
        setDailyProgress([]);
        setSelectedId(null);
        setSelectedDay(null);
        setShowReference(false);
        return;
      }

      try {
        setLoading(true);
        onError('');
        const [entries, dailySummary] = await Promise.all([
          api.getUserProgress(),
          api.getUserProgressDaily(),
        ]);
        if (!active) return;
        setProgressEntries(entries);
        setDailyProgress(dailySummary);
        setSelectedId((previousId) => {
          if (previousId && entries.some((entry) => entry.id === previousId)) {
            return previousId;
          }

          return entries[0]?.id ?? null;
        });
        setShowReference(false);
      } catch (error) {
        if (!active) return;
        onError(error.message || 'Failed to load TaskProgress');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadProgress();

    return () => {
      active = false;
    };
  }, [currentUser, onError]);

  const filteredProgressEntries = useMemo(() => {
    if (!selectedDay) {
      return progressEntries;
    }

    return progressEntries.filter((entry) => formatDayKey(entry.updated_at) === selectedDay);
  }, [progressEntries, selectedDay]);

  useEffect(() => {
    if (!filteredProgressEntries.length) {
      setSelectedId(null);
      return;
    }

    setSelectedId((previousId) => {
      if (previousId && filteredProgressEntries.some((entry) => entry.id === previousId)) {
        return previousId;
      }

      return filteredProgressEntries[0]?.id ?? null;
    });
  }, [filteredProgressEntries]);

  useEffect(() => {
    const hostElement = calendarHostRef.current;

    if (!hostElement) {
      return undefined;
    }

    const updateCalendarWidth = () => {
      setCalendarHostWidth(hostElement.getBoundingClientRect().width);
    };

    updateCalendarWidth();

    if (typeof ResizeObserver === 'function') {
      const observer = new ResizeObserver(() => {
        updateCalendarWidth();
      });

      observer.observe(hostElement);

      return () => {
        observer.disconnect();
      };
    }

    window.addEventListener('resize', updateCalendarWidth);

    return () => {
      window.removeEventListener('resize', updateCalendarWidth);
    };
  }, []);

  const selectedEntry = useMemo(
    () => filteredProgressEntries.find((entry) => entry.id === selectedId) || null,
    [filteredProgressEntries, selectedId],
  );

  const calendarData = useMemo(
    () => buildCalendarData(dailyProgress, calendarYear),
    [dailyProgress, calendarYear],
  );
  const calendarWeekCount = useMemo(
    () => getCalendarWeekCount(calendarYear, CALENDAR_WEEK_START),
    [calendarYear],
  );
  const calendarBlockSize = useMemo(() => {
    if (!calendarHostWidth) {
      return DEFAULT_CALENDAR_BLOCK_SIZE;
    }

    const availableWidth = Math.max(calendarHostWidth - CALENDAR_WEEKDAY_LABEL_SPACE, 0);
    const computedBlockSize =
      Math.floor((availableWidth + CALENDAR_BLOCK_MARGIN) / calendarWeekCount) -
      CALENDAR_BLOCK_MARGIN;

    return Math.max(MIN_CALENDAR_BLOCK_SIZE, Math.min(MAX_CALENDAR_BLOCK_SIZE, computedBlockSize));
  }, [calendarHostWidth, calendarWeekCount]);
  const selectedDayCount = useMemo(
    () => dailyProgress.find((entry) => entry.day === selectedDay)?.completed_tasks ?? 0,
    [dailyProgress, selectedDay],
  );

  if (!currentUser) {
    return (
      <section className="task-progress-empty card reveal">
        <p className="eyebrow">TaskProgress</p>
        <h2>Sign in to view your completed tasks</h2>
        <p className="muted">
          Your saved submissions, scores, and answers appear here after you complete tasks while
          signed in.
        </p>
      </section>
    );
  }

  if (loading && !progressEntries.length) {
    return (
      <section className="task-progress-empty card reveal">
        <p className="eyebrow">TaskProgress</p>
        <h2>Loading your progress</h2>
      </section>
    );
  }

  if (!progressEntries.length) {
    return (
      <section className="task-progress-empty card reveal">
        <p className="eyebrow">TaskProgress</p>
        <h2>No completed tasks yet</h2>
        <p className="muted">Finish a task from the main review page and it will appear here.</p>
      </section>
    );
  }

  return (
    <section className="task-progress-page">
      <section className="task-progress-calendar card reveal">
        <div className="task-progress-calendar-header">
          <div>
            <p className="eyebrow">Daily Tasks</p>
          </div>
          {selectedDay ? (
            <button
              type="button"
              className="ghost task-progress-calendar-clear"
              onClick={() => setSelectedDay(null)}
            >
              Show All Days
            </button>
          ) : null}
        </div>
        <div ref={calendarHostRef} className="task-progress-calendar-grid">
          <ActivityCalendar
            data={calendarData}
            blockSize={calendarBlockSize}
            blockMargin={CALENDAR_BLOCK_MARGIN}
            colorScheme="light"
            fontSize={14}
            labels={{
              totalCount: '{{count}} completed tasks in {{year}}',
              legend: { less: 'Less', more: 'More' },
            }}
            showWeekdayLabels={['mon', 'wed', 'fri']}
            weekStart={CALENDAR_WEEK_START}
            theme={{ light: ['#ebf0f3', '#cdebd6', '#96dbab', '#49be66', '#1f7a35'] }}
            tooltips={{
              activity: {
                text: ({ date, count }) =>
                  `${count} completed ${count === 1 ? 'task' : 'tasks'} on ${date}`,
                withArrow: true,
              },
            }}
            renderBlock={(block, activity) =>
              cloneElement(block, {
                onClick: activity.count
                  ? () =>
                      setSelectedDay((current) =>
                        current === activity.date ? null : activity.date,
                      )
                  : undefined,
                style: {
                  ...block.props.style,
                  cursor: activity.count ? 'pointer' : 'default',
                  stroke: selectedDay === activity.date ? '#ff6b35' : undefined,
                  strokeWidth: selectedDay === activity.date ? 2 : undefined,
                },
              })
            }
          />
        </div>
        <p className="task-progress-calendar-summary muted">
          {selectedDay
            ? `${selectedDay}: ${selectedDayCount} completed ${selectedDayCount === 1 ? 'task' : 'tasks'}`
            : ''}
        </p>
      </section>

      <section className="task-progress-layout">
        <aside className="task-progress-menu card reveal">
          <div className="task-progress-menu-header">
            <p className="eyebrow">Completed Tasks</p>
            <p className="muted">
              {selectedDay ? 'Review submissions completed on the selected calendar day.' : ''}
            </p>
          </div>
          {filteredProgressEntries.length ? (
            <div className="task-progress-list">
              {filteredProgressEntries.map((entry) => {
                const isActive = entry.id === selectedEntry?.id;
                return (
                  <button
                    key={entry.id}
                    type="button"
                    className={`task-progress-item${isActive ? ' task-progress-item-active' : ''}`}
                    onClick={() => {
                      setSelectedId(entry.id);
                      setShowReference(false);
                    }}
                  >
                    <span className="task-progress-item-title">{entry.task.title}</span>
                    <span className="task-progress-item-summary">
                      <span className="task-progress-item-meta">{formatMeta(entry)}</span>
                      {entry.task.complexity ? (
                        <span
                          className={`task-complexity-badge task-progress-item-complexity task-complexity-${entry.task.complexity}`}
                        >
                          {formatComplexity(entry.task.complexity)}
                        </span>
                      ) : null}
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="muted task-progress-calendar-empty">
              No completed tasks were recorded for the selected day.
            </p>
          )}
        </aside>

        <div className="task-progress-detail layout-grid">
          <LeftPanel
            task={selectedEntry?.task}
            progressEntry={selectedEntry}
            aiAnalysis={selectedEntry?.ai_analysis ? { analysis: selectedEntry.ai_analysis } : null}
            aiLoading={false}
          />
          <CodeReviewPanel
            code={selectedEntry?.task.code || ''}
            language={selectedEntry?.task.language || 'python'}
            instructions={selectedEntry?.task.instructions || []}
            responseMode={selectedEntry?.task.submission_mode || 'comments'}
            comments={selectedEntry?.user_comments || []}
            answer={selectedEntry?.user_answer || ''}
            savedAnswer={selectedEntry?.user_answer || ''}
            referenceIssues={showReference ? selectedEntry?.task.reference_issues || [] : []}
            referenceIssueCount={0}
            showReference={showReference}
            onToggleReference={() => setShowReference((value) => !value)}
            onAddComment={() => {}}
            onEditComment={() => {}}
            onAnswerChange={() => {}}
            onSubmitReview={() => {}}
            readOnly
            showHeader={false}
            eyebrowLabel="Code"
          />
        </div>
      </section>
    </section>
  );
}

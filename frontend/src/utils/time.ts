/**
 * Shared time formatting utilities.
 */

export function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return 'No sessions yet';
  const ms = new Date(isoString).getTime();
  if (Number.isNaN(ms)) return 'Unknown';
  // Future timestamps (clock skew) collapse to "Just now"
  const diff = Date.now() - ms;
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface ConfidenceBadgeProps {
  level: "high" | "medium" | "low";
}

export default function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  const badgeClass = {
    high: "badge-high",
    medium: "badge-medium",
    low: "badge-low",
  }[level];

  const label = {
    high: "High Confidence",
    medium: "Medium Confidence",
    low: "Low Confidence",
  }[level];

  return <span className={badgeClass}>{label}</span>;
}
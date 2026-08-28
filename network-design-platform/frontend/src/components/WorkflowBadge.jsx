const STAGE_LABELS = {
  survey: "Survey",
  design: "Design",
  integration: "Integration",
  port_trace: "Port Trace",
  validation: "Validation",
  complete: "Complete",
};

/**
 * Explicit status field, replacing the old workbook's cell-fill-color
 * convention (counted/summed via VBA's GetCellColor/CountCellsByColor)
 * with something that can actually be filtered and queried.
 */
export function WorkflowBadge({ stage }) {
  return <span className={`workflow-badge workflow-badge--${stage}`}>{STAGE_LABELS[stage] ?? stage}</span>;
}

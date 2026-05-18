import { Stack } from "@mui/material";
import CollapsibleList from "../ui/CollapsibleList";

export default function SecurityResult({ security }) {
  const hasAnyIssues =
    security.criticalIssues.length > 0 ||
    security.highIssues.length > 0 ||
    security.mediumIssues.length > 0 ||
    security.lowIssues.length > 0;

  if (!hasAnyIssues) {
    return (
      <CollapsibleList
        title="All Security Checks Passed"
        items={["No security issues were found in the code."]}
        severity="success"
      />
    );
  }

  return (
    <Stack spacing={2}>
      {security.criticalIssues.length > 0 && (
        <CollapsibleList
          title="Critical Security Issues"
          items={security.criticalIssues}
          severity="critical"
        />
      )}

      {security.highIssues.length > 0 && (
        <CollapsibleList
          title="High Priority Issues"
          items={security.highIssues}
          severity="high" // Changed from "error" to "high" to get the orange color
        />
      )}

      {security.mediumIssues.length > 0 && (
        <CollapsibleList
          title="Medium Priority Issues"
          items={security.mediumIssues}
          severity="medium" // Changed from "warning" to "medium" to get the yellow color with warning icon
        />
      )}

      {security.lowIssues.length > 0 && (
        <CollapsibleList
          title="Low Priority Issues"
          items={security.lowIssues}
          severity="low" // Changed from "info" to "low" to match term used in ValidationsStats
        />
      )}
    </Stack>
  );
}

import { Stack } from "@mui/material";
import CollapsibleList from "../ui/CollapsibleList";

export default function QualityResult({ quality }) {
  return (
    <Stack spacing={2}>
      {quality.issues?.length > 0 && (
        <CollapsibleList
          title="Issues"
          items={quality.issues}
          severity="error"
        />
      )}

      {quality.recommendations?.length > 0 && (
        <CollapsibleList
          title="Recommendations"
          items={quality.recommendations}
          severity="warning"
        />
      )}
    </Stack>
  );
}

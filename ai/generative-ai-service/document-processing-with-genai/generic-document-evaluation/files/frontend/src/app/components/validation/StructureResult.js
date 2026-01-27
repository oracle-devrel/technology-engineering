import { Stack } from "@mui/material";
import CollapsibleList from "../ui/CollapsibleList";

export default function StructureResult({ structure, level, input, filePath }) {
  return (
    <Stack spacing={2}>
      {structure.issues?.length > 0 && (
        <CollapsibleList
          title="Issues"
          items={structure.issues}
          severity="error"
        />
      )}

      {structure.recommendations?.length > 0 && (
        <CollapsibleList
          title="Recommendations"
          items={structure.recommendations}
          severity="warning"
        />
      )}
    </Stack>
  );
}

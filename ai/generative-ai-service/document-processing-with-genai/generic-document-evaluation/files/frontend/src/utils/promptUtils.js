export const loadPrompt = async (promptName) => {
  const res = await fetch(`/prompts/${promptName}.txt`);
  if (!res.ok) throw new Error(`Failed to load prompt: ${promptName}`);
  return res.text();
};

export const checkPromptExists = async (promptName) => {
  const res = await fetch(`/prompts/${promptName}.txt`, { method: "HEAD" });
  return res.ok;
};

export const preparePrompt = async (promptName, replacements = {}) => {
  let promptContent = await loadPrompt(promptName);
  for (const [key, value] of Object.entries(replacements)) {
    promptContent = promptContent.replace(
      new RegExp(`\\{${key}\\}`, "g"),
      value != null ? String(value) : ""
    );
  }
  return promptContent;
};

export const loadAllPrompts = async () => {
  const required = [
    "quality_checker_prompt",
  ];
  const missing = [];
  for (const name of required) {
    if (!(await checkPromptExists(name))) missing.push(name);
  }
  if (missing.length) throw new Error(`Missing prompts: ${missing.join(", ")}`);
  const prompts = {};
  for (const name of required) {
    prompts[name] = await loadPrompt(name);
  }
  return prompts;
};

export const processJsonResponse = (jsonResponse) => {
  const start = jsonResponse.indexOf("{");
  const end = jsonResponse.lastIndexOf("}") + 1;
  if (start === -1 || end === 0) throw new Error("Invalid JSON response");
  return JSON.parse(jsonResponse.slice(start, end));
};

export const looksLikeJson = (response) => {
  const cleanResponse = response.replace(/```json\n|\n```/g, "").trim();

  return cleanResponse.startsWith("{") && cleanResponse.endsWith("}");
};

export const buildErrorResponse = (promptName, errorMessage) => {
  switch (promptName) {
    case "quality_checker_prompt":
      return JSON.stringify({
        issues: [`Error processing response: ${errorMessage}`],
        recommendations: ["Try again or check the file manually"],
        qualityScore: 1,
      });
    default:
      return JSON.stringify({ error: errorMessage });
  }
};

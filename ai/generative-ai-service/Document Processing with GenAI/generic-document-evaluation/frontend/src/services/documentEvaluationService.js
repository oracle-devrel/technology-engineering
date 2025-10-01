const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function uploadDocuments(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE_URL}/upload-documents`, {
    method: "POST",
    body: formData,
  });

  return response.json();
}

export async function evaluateDocuments(
  criteriaFile = null,
  criteriaJson = null,
  additionalInstructions = null
) {
  const formData = new FormData();

  if (criteriaFile) {
    formData.append("criteria_file", criteriaFile);
  } else if (criteriaJson) {
    formData.append("criteria_json", JSON.stringify(criteriaJson));
  }

  if (additionalInstructions) {
    formData.append("additional_instruction", additionalInstructions);
  }

  const response = await fetch(`${API_BASE_URL}/evaluate`, {
    method: "POST",
    body: formData,
  });

  return response.json();
}

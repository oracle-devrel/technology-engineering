"use client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
console.log("API_BASE_URL:", API_BASE_URL);

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Request failed: ${url}`, error);
    throw error;
  }
}

export default {
  request,
};

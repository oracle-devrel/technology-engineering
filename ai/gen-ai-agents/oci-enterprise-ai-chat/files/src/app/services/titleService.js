const API_URL = '/api/generate-title';

export async function generateTitle(userMessage, assistantResponse) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userMessage, assistantResponse })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Title API error:', response.status, errorData);
      return null;
    }

    const data = await response.json();
    console.log('Generated title:', data.title);
    return data.title || null;
  } catch (error) {
    console.error('Title generation failed:', error);
    return null;
  }
}

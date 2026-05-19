import { NextResponse } from 'next/server';
import { ociRequest } from '../../lib/oci-proxy';
import { createLogger } from '../../lib/logger';

export async function POST(request) {
  const requestId = crypto.randomUUID();
  const log = createLogger('generate-title-api', { requestId });

  try {
    const { userMessage } = await request.json();

    if (!userMessage) {
      return NextResponse.json({ error: 'userMessage is required' }, { status: 400 });
    }

    const prompt = `Convert to a clean 2-4 word title (fix typos):
"tell me a jok" → "Joke Request"
"whats the wether" → "Weather Inquiry"
"${userMessage.substring(0, 150)}" → "`;

    const requestBody = {
      model: 'openai.gpt-4o-mini',
      input: [{ role: 'user', content: prompt }],
      stream: false
    };

    const response = await ociRequest('POST', '/responses', { body: requestBody });

    if (!response.ok) {
      const errorText = await response.text();
      log.error('OCI API error', { status: response.status, error: errorText });
      return NextResponse.json({ error: 'Failed to generate title' }, { status: response.status });
    }

    const data = await response.json();
    log.debug('OCI title response', { data: JSON.stringify(data) });

    let rawText = '';
    if (typeof data.output === 'string') {
      rawText = data.output;
    } else if (Array.isArray(data.output)) {
      const textOutput = data.output.find(o => o.type === 'message' || o.content);
      if (textOutput?.content) {
        if (Array.isArray(textOutput.content)) {
          const textContent = textOutput.content.find(c => c.type === 'output_text' || c.text);
          rawText = textContent?.text || textContent?.output_text || '';
        } else {
          rawText = textOutput.content;
        }
      }
    } else if (data.choices?.[0]?.message?.content) {
      rawText = data.choices[0].message.content;
    } else if (data.text) {
      rawText = data.text;
    }

    // Extract title from response - look for the actual title
    let title = rawText;

    // Look for quoted title
    const quotedMatch = rawText.match(/"([^"]{2,40})"/);
    if (quotedMatch) {
      title = quotedMatch[1];
    } else if (rawText.includes('\n')) {
      // Take last non-empty line
      const lines = rawText.split('\n').map(l => l.trim()).filter(l => l);
      title = lines[lines.length - 1];
    }

    // Clean up
    title = title.replace(/^["']|["']$/g, '').trim();
    title = title.replace(/[.!?:,]+$/, '').trim();

    // Remove reasoning prefixes
    title = title.replace(/^(thus|so|therefore|the title is|title|answer|output|result)[\s:]+/i, '').trim();

    // Limit to 5 words max
    const words = title.split(/\s+/);
    if (words.length > 5) {
      title = words.slice(0, 5).join(' ');
    }

    // Fallback if extraction failed
    if (!title || title.length < 2 || title.toLowerCase().includes('summarize') || title.toLowerCase().includes('message')) {
      const fallbackWords = userMessage.split(/\s+/).slice(0, 4);
      title = fallbackWords.map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
      title = title.replace(/[?!.,]+$/, '');
    }

    return NextResponse.json({ title });

  } catch (error) {
    log.error('Generate title error', { error: error.message });
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

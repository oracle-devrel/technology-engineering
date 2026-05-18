import { NextResponse } from 'next/server';
import { ociRequest } from '../../lib/oci-proxy';
import { createLogger } from '../../lib/logger';

// POST - Create a conversation or add item to existing
export async function POST(request) {
  const requestId = crypto.randomUUID();
  const log = createLogger('conversations-api', { requestId });

  try {
    const { searchParams } = new URL(request.url);
    const addItemToConv = searchParams.get('addItemTo');

    const body = await request.json();

    // If adding item to existing conversation
    if (addItemToConv) {
      // Formato correcto: wrapper "items" con array de mensajes
      const itemBody = {
        items: Array.isArray(body.items) ? body.items : [
          {
            type: "message",
            role: body.role || "user",
            content: body.content
          }
        ]
      };

      log.info('Adding items to conversation', { conversationId: addItemToConv, body: JSON.stringify(itemBody) });

      const response = await ociRequest('POST', `/conversations/${addItemToConv}/items`, { body: itemBody });

      const text = await response.text();
      log.info('Add items response', { status: response.status, response: text });

      if (response.ok) {
        try {
          return NextResponse.json(JSON.parse(text));
        } catch (e) {
          return NextResponse.json({ success: true, raw: text });
        }
      }
      return NextResponse.json({ error: text, status: response.status }, { status: response.status });
    }

    const { metadata, items } = body;

    const requestBody = {
      metadata: metadata || { topic: "test" },
      items: items || [{ type: "message", role: "user", content: "Hello!" }],
    };

    // Try different base paths for creating conversations (openai first since it worked)
    const results = [];

    for (const basePath of ['/openai/v1', '/v1']) {
      log.info('Trying POST conversation', { basePath });

      try {
        const response = await ociRequest('POST', '/conversations', { body: requestBody, basePath });

        const text = await response.text();
        log.info('POST conversation response', { basePath, status: response.status, response: text.substring(0, 500) });

        results.push({
          basePath,
          status: response.status,
          success: response.ok,
          data: response.ok ? JSON.parse(text) : text,
        });

        if (response.ok) {
          return NextResponse.json(JSON.parse(text));
        }
      } catch (error) {
        log.error('POST conversation error', { basePath, error: error.message });
        results.push({
          basePath,
          success: false,
          error: error.message,
        });
      }
    }

    return NextResponse.json({
      error: 'All endpoints failed',
      results,
    }, { status: 404 });

  } catch (error) {
    log.error('Conversation POST error', { error: error.message });
    return NextResponse.json(
      { error: error.message || 'Failed to create conversation' },
      { status: 500 }
    );
  }
}

// GET - Test all possible endpoints for listing conversations/responses
export async function GET(request) {
  const requestId = crypto.randomUUID();
  const log = createLogger('conversations-api', { requestId });

  try {
    const { searchParams } = new URL(request.url);

    // Get specific conversation by ID
    const conversationId = searchParams.get('id');
    const responseId = searchParams.get('responseId');
    const getItems = searchParams.get('getItems') === 'true';

    // Test getting a response by its ID
    if (responseId) {
      log.info('GET response by ID', { responseId });

      const results = [];
      for (const basePath of ['/v1', '/openai/v1']) {
        for (const path of [`/responses/${responseId}`, `/responses/${responseId}?include=conversation.item`]) {
          log.debug('Trying response endpoint', { basePath, path });

          try {
            const response = await ociRequest('GET', path, { basePath });

            const text = await response.text();
            log.debug('Response endpoint result', { basePath, path, status: response.status, response: text.substring(0, 500) });

            results.push({
              basePath,
              path,
              status: response.status,
              success: response.ok,
              data: response.ok ? JSON.parse(text) : text.substring(0, 300),
            });

            if (response.ok) {
              return NextResponse.json({
                success: true,
                data: JSON.parse(text),
              });
            }
          } catch (error) {
            log.error('Response endpoint error', { basePath, path, error: error.message });
            results.push({
              basePath,
              path,
              success: false,
              error: error.message,
            });
          }
        }
      }

      return NextResponse.json({
        error: 'Could not retrieve response from any endpoint',
        testedResponseId: responseId,
        results,
      }, { status: 404 });
    }

    if (conversationId) {
      // If getItems is requested, try items endpoints
      if (getItems) {
        const results = [];
        for (const basePath of ['/openai/v1', '/v1']) {
          log.info('Get conversation items', { basePath, conversationId });

          try {
            // Paginate: fetch all items using limit + after cursor
            let allItems = [];
            let afterCursor = null;
            let pageCount = 0;
            const MAX_PAGES = 20; // Safety limit

            while (pageCount < MAX_PAGES) {
              let queryString = `?limit=100`;
              if (afterCursor) {
                queryString += `&after=${afterCursor}`;
              }

              const response = await ociRequest('GET', `/conversations/${conversationId}/items${queryString}`, { basePath });

              const text = await response.text();
              log.debug('Items page response', { basePath, status: response.status, response: text.substring(0, 300) });

              if (!response.ok) {
                results.push({
                  basePath,
                  status: response.status,
                  success: false,
                  data: text.substring(0, 200),
                });
                break;
              }

              const parsed = JSON.parse(text);
              const pageItems = parsed.data || [];
              allItems = allItems.concat(pageItems);
              pageCount++;

              log.debug('Items pagination', { page: pageCount, pageItems: pageItems.length, total: allItems.length, hasMore: parsed.has_more });

              if (!parsed.has_more || pageItems.length === 0) {
                // All items fetched - return combined result
                return NextResponse.json({ data: allItems });
              }

              // Use last_id as cursor for next page
              afterCursor = parsed.last_id || pageItems[pageItems.length - 1]?.id;
              if (!afterCursor) break;
            }

            // If we got items but hit the page limit, return what we have
            if (allItems.length > 0) {
              log.info('Returning paginated items', { itemCount: allItems.length, pages: pageCount });
              return NextResponse.json({ data: allItems });
            }
          } catch (error) {
            log.error('Error fetching items', { basePath, error: error.message });
            results.push({
              basePath,
              success: false,
              error: error.message,
            });
          }
        }

        return NextResponse.json({
          error: 'Could not retrieve conversation items from any endpoint',
          results,
        }, { status: 404 });
      }

      // Try to get the conversation itself
      for (const basePath of ['/openai/v1', '/v1']) {
        log.info('Get conversation', { basePath, conversationId });

        const response = await ociRequest('GET', `/conversations/${conversationId}`, { basePath });

        if (response.ok) {
          const data = await response.json();
          log.debug('Conversation response', { data: JSON.stringify(data).substring(0, 1000) });
          return NextResponse.json(data);
        } else {
          const errorText = await response.text();
          log.warn('Get conversation failed', { basePath, status: response.status, error: errorText.substring(0, 200) });
        }
      }

      return NextResponse.json(
        { error: 'Could not retrieve conversation from any endpoint' },
        { status: 404 }
      );
    }

    // Default: Try listing conversations from multiple endpoints
    for (const basePath of ['/openai/v1', '/v1']) {
      log.info('List conversations', { basePath });

      const response = await ociRequest('GET', '/conversations', { basePath });

      if (response.ok) {
        const data = await response.json();
        log.debug('List conversations response', { data: JSON.stringify(data).substring(0, 1000) });
        return NextResponse.json(data);
      } else {
        const errorText = await response.text();
        log.warn('List conversations failed', { basePath, status: response.status, error: errorText.substring(0, 200) });
      }
    }

    return NextResponse.json(
      { error: 'Could not list conversations from any endpoint' },
      { status: 404 }
    );

  } catch (error) {
    log.error('Conversation GET error', { error: error.message });
    return NextResponse.json(
      { error: error.message || 'Failed to fetch' },
      { status: 500 }
    );
  }
}

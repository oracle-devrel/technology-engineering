/**
 * Conversation Storage Service
 *
 * Abstraction layer for storing conversation metadata.
 * Currently uses localStorage, but designed to easily swap to a database.
 *
 * To switch to a database in the future:
 * 1. Create a new adapter (e.g., DatabaseAdapter)
 * 2. Change the STORAGE_ADAPTER constant
 * 3. Implement the same interface methods
 */

let STORAGE_KEY = 'oci_conversations';
const STORAGE_VERSION = '1.0';
let _currentUserId = null;

/**
 * Generate a UUID for URL-friendly conversation IDs
 */
function generateUrlId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// ============================================
// Storage Adapter Interface
// ============================================

/**
 * LocalStorage Adapter
 * Implements conversation storage using browser localStorage
 */
const LocalStorageAdapter = {
  name: 'localStorage',

  async getAll() {
    if (typeof window === 'undefined') return [];
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      const parsed = JSON.parse(data);
      // Validate version
      if (parsed.version !== STORAGE_VERSION) {
        console.warn('Storage version mismatch, migrating...');
        return this._migrate(parsed);
      }
      return parsed.conversations || [];
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return [];
    }
  },

  async save(conversations) {
    if (typeof window === 'undefined') return false;
    try {
      const data = {
        version: STORAGE_VERSION,
        updatedAt: new Date().toISOString(),
        conversations,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
      return false;
    }
  },

  async clear() {
    if (typeof window === 'undefined') return false;
    try {
      localStorage.removeItem(STORAGE_KEY);
      return true;
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
      return false;
    }
  },

  _migrate(oldData) {
    // Handle migration from older versions if needed
    // For now, just return empty array for incompatible versions
    return oldData.conversations || [];
  },
};

/**
 * Database Adapter (placeholder for future implementation)
 * Uncomment and implement when ready to switch to database
 */
// const DatabaseAdapter = {
//   name: 'database',
//
//   async getAll() {
//     const response = await fetch('/api/conversations/stored');
//     return response.json();
//   },
//
//   async save(conversations) {
//     await fetch('/api/conversations/stored', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ conversations }),
//     });
//     return true;
//   },
//
//   async clear() {
//     await fetch('/api/conversations/stored', { method: 'DELETE' });
//     return true;
//   },
// };

// ============================================
// Current Adapter Selection
// ============================================

// Change this to switch storage backends
const STORAGE_ADAPTER = LocalStorageAdapter;

// ============================================
// Write serialization to prevent race conditions
// ============================================

let _writeLock = Promise.resolve();

const withWriteLock = (fn) => {
  const result = _writeLock.then(fn);
  _writeLock = result.catch(() => {});
  return result;
};

// ============================================
// Conversation Storage Service
// ============================================

/**
 * @typedef {Object} StoredConversation
 * @property {string} id - OCI conversation ID (conv_xxx)
 * @property {string} urlId - UUID for URL-friendly identification
 * @property {string} title - Display title for the conversation
 * @property {string} createdAt - ISO timestamp
 * @property {string} updatedAt - ISO timestamp
 * @property {string} [lastMessage] - Preview of last message
 * @property {string} [lastResponseId] - Last response ID for context continuity
 * @property {number} [messageCount] - Number of messages
 * @property {Object} [metadata] - Additional metadata from OCI
 */

const ConversationStorage = {
  /**
   * Get all stored conversations, sorted by most recent
   * @returns {Promise<StoredConversation[]>}
   */
  async list() {
    const conversations = await STORAGE_ADAPTER.getAll();
    return conversations.sort((a, b) =>
      new Date(b.updatedAt) - new Date(a.updatedAt)
    );
  },

  /**
   * Get a specific conversation by OCI ID
   * @param {string} id - OCI Conversation ID
   * @returns {Promise<StoredConversation|null>}
   */
  async get(id) {
    const conversations = await STORAGE_ADAPTER.getAll();
    return conversations.find(c => c.id === id) || null;
  },

  /**
   * Get a specific conversation by URL ID (UUID)
   * @param {string} urlId - URL-friendly UUID
   * @returns {Promise<StoredConversation|null>}
   */
  async getByUrlId(urlId) {
    const conversations = await STORAGE_ADAPTER.getAll();
    return conversations.find(c => c.urlId === urlId) || null;
  },

  /**
   * Add a new conversation
   * @param {Object} params
   * @param {string} params.id - OCI conversation ID
   * @param {string} [params.title] - Display title
   * @param {Object} [params.metadata] - Additional metadata
   * @returns {Promise<StoredConversation>}
   */
  async add({ id, title, metadata = {} }) {
    return withWriteLock(async () => {
      const conversations = await STORAGE_ADAPTER.getAll();

      // Check if already exists
      const existing = conversations.find(c => c.id === id);
      if (existing) {
        return existing;
      }

      const newConversation = {
        id,
        urlId: generateUrlId(),
        title: title || this._generateTitle(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        lastMessage: null,
        messageCount: 0,
        metadata,
      };

      conversations.unshift(newConversation);
      await STORAGE_ADAPTER.save(conversations);

      return newConversation;
    });
  },

  /**
   * Update an existing conversation
   * @param {string} id - Conversation ID
   * @param {Partial<StoredConversation>} updates - Fields to update
   * @returns {Promise<StoredConversation|null>}
   */
  async update(id, updates) {
    return withWriteLock(async () => {
      const conversations = await STORAGE_ADAPTER.getAll();
      const index = conversations.findIndex(c => c.id === id);

      if (index === -1) {
        return null;
      }

      conversations[index] = {
        ...conversations[index],
        ...updates,
        updatedAt: new Date().toISOString(),
      };

      await STORAGE_ADAPTER.save(conversations);
      return conversations[index];
    });
  },

  /**
   * Delete a conversation
   * @param {string} id - Conversation ID
   * @returns {Promise<boolean>}
   */
  async delete(id) {
    if (typeof window === 'undefined') return false;
    try {
      // Direct synchronous localStorage access to avoid any async race conditions
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return false;

      const data = JSON.parse(raw);
      const conversations = data.conversations || [];
      const filtered = conversations.filter(c => c.id !== id);

      if (filtered.length === conversations.length) {
        console.warn('[ConversationStorage] delete: id not found:', id);
        return false;
      }

      data.conversations = filtered;
      data.updatedAt = new Date().toISOString();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

      // Verify deletion persisted
      const verify = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (verify?.conversations?.some(c => c.id === id)) {
        console.error('[ConversationStorage] delete: verification failed, retrying');
        verify.conversations = verify.conversations.filter(c => c.id !== id);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(verify));
      }

      console.log(`[ConversationStorage] delete: removed ${id}, ${filtered.length} remaining`);
      return true;
    } catch (error) {
      console.error('[ConversationStorage] delete failed:', error);
      return false;
    }
  },

  /**
   * Clear all stored conversations
   * @returns {Promise<boolean>}
   */
  async clearAll() {
    return STORAGE_ADAPTER.clear();
  },

  /**
   * Get recent conversations (limit N)
   * @param {number} limit - Maximum number to return
   * @returns {Promise<StoredConversation[]>}
   */
  async getRecent(limit = 10) {
    const conversations = await this.list();
    return conversations.slice(0, limit);
  },

  /**
   * Get a page of conversations (for infinite scroll)
   * @returns {Promise<{items: StoredConversation[], total: number, hasMore: boolean}>}
   */
  async getPage(offset = 0, limit = 20) {
    const conversations = await this.list();
    const items = conversations.slice(offset, offset + limit);
    return {
      items,
      total: conversations.length,
      hasMore: offset + limit < conversations.length,
    };
  },

  /**
   * Generate a default title based on date/time
   * @private
   */
  _generateTitle() {
    const now = new Date();
    return `Conversation ${now.toLocaleDateString()} ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  },

  /**
   * Set user ID for storage isolation.
   * Each user gets their own localStorage key.
   * @param {string|null} userId
   */
  setUserId(userId) {
    _currentUserId = userId || null;
    STORAGE_KEY = userId ? `oci_conversations_${userId}` : 'oci_conversations';
  },

  /**
   * Initialize from session — fetches /api/auth/session and sets user ID
   * @returns {Promise<void>}
   */
  async initFromSession() {
    if (_currentUserId) return;
    try {
      const res = await fetch('/api/auth/session');
      const data = await res.json();
      if (data.authenticated && data.user?.email) {
        this.setUserId(data.user.email);
      }
    } catch {
      // Auth not available, use default key
    }
  },

  /**
   * Get storage adapter info (for debugging)
   */
  getAdapterInfo() {
    return {
      name: STORAGE_ADAPTER.name,
      version: STORAGE_VERSION,
      userId: _currentUserId,
    };
  },
};

export default ConversationStorage;

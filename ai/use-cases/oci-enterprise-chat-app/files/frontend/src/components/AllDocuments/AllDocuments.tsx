import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Eye,
  MessageSquare,
  Trash2,
  Upload,
} from 'lucide-react';
import { api } from '../../services/api';
import { Document, User } from '../../types';

interface AllDocumentsProps {
  user: User;
  onViewDocument: (document: Document) => void;
  onChatWithDocuments: (documents: Document[]) => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const statusConfig: Record<string, { label: string; className: string }> = {
  completed: { label: 'Completed', className: 'text-green-400 bg-green-400/10' },
  processing: { label: 'Processing', className: 'text-amber-400 bg-amber-400/10' },
  failed: { label: 'Failed', className: 'text-red-400 bg-red-400/10' },
  uploaded: { label: 'Uploaded', className: 'text-blue-400 bg-blue-400/10' },
};

const AllDocuments: React.FC<AllDocumentsProps> = ({
  user,
  onViewDocument,
  onChatWithDocuments,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());

  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const docs = await api.listDocuments();
      setDocuments(docs);
      setError(null);
    } catch {
      setError('Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const filteredDocs = documents.filter((doc) => {
    if (!searchQuery.trim()) return true;
    return doc.metadata.filename.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleDelete = async (docId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.deleteDocument(docId);
      setSelectedDocs((prev) => { const n = new Set(prev); n.delete(docId); return n; });
      await loadDocuments();
    } catch {
      setError('Failed to delete document');
    }
  };

  const toggleSelect = (docId: string) => {
    setSelectedDocs((prev) => {
      const n = new Set(prev);
      if (n.has(docId)) n.delete(docId); else n.add(docId);
      return n;
    });
  };

  const handleChatSelected = () => {
    const docs = documents.filter((d) => selectedDocs.has(d.id));
    if (docs.length > 0) onChatWithDocuments(docs);
  };

  const completedCount = documents.filter((d) => d.status === 'completed').length;
  const totalSize = documents.reduce((s, d) => s + d.metadata.file_size, 0);

  return (
    <div className="flex-1 overflow-auto bg-dark-900 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">All Documents</h1>
          <p className="text-dark-400 text-sm mt-1">
            {documents.length} document{documents.length !== 1 ? 's' : ''} &middot;{' '}
            {completedCount} completed &middot; {formatFileSize(totalSize)} total
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectedDocs.size > 0 && (
            <button
              onClick={handleChatSelected}
              className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              Chat with {selectedDocs.size}
            </button>
          )}
          <button
            onClick={loadDocuments}
            className="p-2 text-dark-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-dark-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search documents..."
          className="w-full pl-10 pr-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-900/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <svg className="animate-spin h-8 w-8 text-oracle-red" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="bg-dark-800 rounded-xl border border-dark-700 p-12 text-center">
          <FileText className="h-12 w-12 text-dark-600 mx-auto mb-3" />
          <h3 className="text-white font-medium mb-1">
            {searchQuery ? 'No matching documents' : 'No documents yet'}
          </h3>
          <p className="text-dark-400 text-sm">
            {searchQuery
              ? `No documents match "${searchQuery}"`
              : 'Upload documents through a project to get started'}
          </p>
        </div>
      ) : (
        <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700">
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedDocs.size === filteredDocs.length && filteredDocs.length > 0}
                    onChange={(e) => {
                      setSelectedDocs(e.target.checked ? new Set(filteredDocs.map((d) => d.id)) : new Set());
                    }}
                    className="w-4 h-4 rounded border-dark-600 bg-dark-700 accent-oracle-red"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wide">Document</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wide">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wide">Size</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wide">Uploaded</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-dark-400 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.map((doc) => {
                const st = statusConfig[doc.status] || statusConfig.uploaded;
                return (
                  <tr key={doc.id} className="border-b border-dark-700 last:border-b-0 hover:bg-dark-700/50 transition-colors">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedDocs.has(doc.id)}
                        onChange={() => toggleSelect(doc.id)}
                        className="w-4 h-4 rounded border-dark-600 bg-dark-700 accent-oracle-red"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-oracle-red/15 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FileText className="w-4 h-4 text-oracle-red" />
                        </div>
                        <span className="text-white text-sm font-medium truncate max-w-xs">
                          {doc.metadata.filename}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${st.className}`}>
                        {st.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-dark-300 text-sm">{formatFileSize(doc.metadata.file_size)}</td>
                    <td className="px-4 py-3 text-dark-300 text-sm">{formatDate(doc.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => onViewDocument(doc)}
                          className="p-1.5 text-dark-400 hover:text-white hover:bg-dark-600 rounded-md transition-colors"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onChatWithDocuments([doc])}
                          className="p-1.5 text-dark-400 hover:text-oracle-red hover:bg-dark-600 rounded-md transition-colors"
                          title="Chat"
                        >
                          <MessageSquare className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-dark-600 rounded-md transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary stats */}
      {searchQuery && filteredDocs.length < documents.length && (
        <p className="text-sm text-dark-400 mt-3">
          Showing {filteredDocs.length} of {documents.length} document{documents.length !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  );
};

export default AllDocuments;

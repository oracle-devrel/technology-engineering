import React from 'react';
import { HelpCircle, Mail, ExternalLink, BookOpen } from 'lucide-react';

const HelpSupport: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <HelpCircle className="h-8 w-8 text-oracle-red" />
            <h1 className="text-2xl font-bold text-white">Help & Support</h1>
          </div>
          <p className="text-dark-300">
            Get help with the AI-Q Enterprise platform or reach out to our support team.
          </p>
        </div>

        <div className="grid gap-6">
          {/* Contact Support */}
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-lg bg-oracle-red/20 flex items-center justify-center">
                <Mail className="h-5 w-5 text-oracle-red" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Contact Support</h2>
                <p className="text-sm text-dark-300">Reach out to our support team for assistance</p>
              </div>
            </div>
            <p className="text-dark-200 mb-4">
              If you need help with the platform, have questions, or want to report an issue,
              please contact our support team via email.
            </p>
            <a
              href="mailto:aiq-support@example.com"
              className="inline-flex items-center gap-2 px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white rounded-lg transition-colors"
            >
              <Mail className="h-4 w-4" />
              aiq-support@example.com
            </a>
          </div>

          {/* OCI Documentation */}
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <BookOpen className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">OCI Documentation</h2>
                <p className="text-sm text-dark-300">Oracle Cloud Infrastructure guides and references</p>
              </div>
            </div>
            <p className="text-dark-200 mb-4">
              Visit the official Oracle Cloud Infrastructure documentation for detailed guides,
              API references, and best practices.
            </p>
            <a
              href="https://docs.oracle.com/en-us/iaas/Content/home.htm"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg border border-dark-600 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
              OCI Documentation
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpSupport;

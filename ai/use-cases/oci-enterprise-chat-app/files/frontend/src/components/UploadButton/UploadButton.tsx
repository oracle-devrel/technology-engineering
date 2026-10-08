import React, { useRef } from 'react';

interface UploadButtonProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

const UploadButton: React.FC<UploadButtonProps> = ({ onFileSelect, disabled }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      onFileSelect(file);
      // Reset input so the same file can be selected again
      event.target.value = '';
    } else if (file) {
      alert('Please select a PDF file');
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />
      <button
        onClick={handleClick}
        disabled={disabled}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg font-semibold
          transition-all duration-200
          ${
            disabled
              ? 'bg-dark-600 text-dark-400 cursor-not-allowed opacity-60'
              : 'bg-oracle-red hover:bg-oracle-red-dark text-white shadow-oracle hover:shadow-lg'
          }
          focus:outline-none focus:ring-2 focus:ring-oracle-red focus:ring-offset-2 focus:ring-offset-dark-800
        `}
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <span>Upload PDF</span>
      </button>
    </>
  );
};

export default UploadButton;

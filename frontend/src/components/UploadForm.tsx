'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import { uploadPDF } from '@/lib/api';

interface UploadFormProps {
  onUploadSuccess: () => void;
}

export default function UploadForm({ onUploadSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      if (selectedFile.type !== 'application/pdf') {
        toast.error('Please upload a PDF file');
        return;
      }
      setFile(selectedFile);
      // Auto-fill title from filename
      if (!title) {
        setTitle(selectedFile.name.replace('.pdf', ''));
      }
    }
  }, [title]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      toast.error('Please select a PDF file');
      return;
    }

    if (!title.trim()) {
      toast.error('Please enter a title');
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      await uploadPDF(file, title.trim(), description.trim() || undefined, (p) => {
        setProgress(p);
      });

      toast.success('PDF uploaded successfully! Processing...');
      setFile(null);
      setTitle('');
      setDescription('');
      onUploadSuccess();
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload PDF. Please try again.');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const removeFile = () => {
    setFile(null);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Create Podcast from PDF</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          {file ? (
            <div className="flex items-center justify-center space-x-3">
              <span className="text-4xl">📄</span>
              <div className="text-left">
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              {!uploading && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile();
                  }}
                  className="ml-4 text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              )}
            </div>
          ) : (
            <div>
              <span className="text-4xl">📁</span>
              <p className="mt-2 text-gray-600">
                {isDragActive
                  ? 'Drop the PDF here...'
                  : 'Drag & drop a PDF file here, or click to select'}
              </p>
              <p className="text-sm text-gray-400 mt-1">PDF files only, max 10MB</p>
            </div>
          )}
        </div>

        {/* Title Input */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Podcast Title *
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a title for your podcast"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow"
            disabled={uploading}
          />
        </div>

        {/* Description Input */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add a description for your podcast"
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-shadow resize-none"
            disabled={uploading}
          />
        </div>

        {/* Upload Progress */}
        {uploading && progress > 0 && (
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!file || !title.trim() || uploading}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            !file || !title.trim() || uploading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {uploading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Uploading... {progress}%
            </span>
          ) : (
            '🎙️ Create Podcast'
          )}
        </button>
      </form>
    </div>
  );
}
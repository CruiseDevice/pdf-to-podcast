'use client';

import { useState, useCallback } from 'react';
import UploadForm from '@/components/UploadForm';
import PodcastList from '@/components/PodcastList';

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = useCallback(() => {
    // Trigger a refresh of the podcast list
    setRefreshKey((prev) => prev + 1);
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🎙️</span>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PDF to Podcast</h1>
              <p className="text-sm text-gray-500">Convert your PDF documents into engaging audio</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Upload Section */}
        <section className="bg-white rounded-xl shadow-sm p-6">
          <UploadForm onUploadSuccess={handleUploadSuccess} />
        </section>

        {/* Divider */}
        <div className="border-t border-gray-200"></div>

        {/* Podcast List Section */}
        <section>
          <PodcastList key={refreshKey} />
        </section>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-16">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          PDF to Podcast Converter • Powered by AI
        </div>
      </footer>
    </main>
  );
}
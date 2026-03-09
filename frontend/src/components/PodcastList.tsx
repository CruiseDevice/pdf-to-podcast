'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Podcast, listPodcasts, deletePodcast, getPodcastStatus, getAudioUrl } from '@/lib/api';

export default function PodcastList() {
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPodcasts = async () => {
    try {
      const data = await listPodcasts();
      setPodcasts(data);
    } catch (error) {
      console.error('Failed to fetch podcasts:', error);
      toast.error('Failed to load podcasts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPodcasts();
  }, []);

  // Poll for status updates on processing podcasts
  useEffect(() => {
    const processingPodcasts = podcasts.filter(
      (p) => p.status === 'pending' || p.status === 'processing'
    );

    if (processingPodcasts.length === 0) return;

    const interval = setInterval(async () => {
      for (const podcast of processingPodcasts) {
        try {
          const status = await getPodcastStatus(podcast.id);
          if (status.status !== podcast.status) {
            setPodcasts((prev) =>
              prev.map((p) =>
                p.id === podcast.id
                  ? { ...p, status: status.status as Podcast['status'], audio_url: status.audio_url, error: status.error }
                  : p
              )
            );
            if (status.status === 'completed') {
              toast.success(`${podcast.filename} is ready!`);
            } else if (status.status === 'failed') {
              toast.error(`${podcast.filename} failed to process`);
            }
          }
        } catch (error) {
          console.error('Failed to check status:', error);
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [podcasts]);

  const handleDelete = async (podcastId: string, filename: string) => {
    if (!confirm(`Delete "${filename}"?`)) return;

    try {
      await deletePodcast(podcastId);
      setPodcasts((prev) => prev.filter((p) => p.id !== podcastId));
      toast.success('Podcast deleted');
    } catch (error) {
      console.error('Failed to delete podcast:', error);
      toast.error('Failed to delete podcast');
    }
  };

  const getStatusBadge = (status: Podcast['status']) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="text-center py-10 text-gray-500">
        Loading podcasts...
      </div>
    );
  }

  if (podcasts.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500">
        No podcasts yet. Upload a PDF to get started!
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Your Podcasts</h2>
      <div className="space-y-3">
        {podcasts.map((podcast) => (
          <div
            key={podcast.id}
            className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm border border-gray-200"
          >
            <div className="flex items-center space-x-4">
              <div className="text-2xl">🎙️</div>
              <div>
                <p className="font-medium text-gray-900">{podcast.filename}</p>
                <div className="flex items-center space-x-2 mt-1">
                  {getStatusBadge(podcast.status)}
                  <span className="text-xs text-gray-500">
                    {new Date(podcast.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {podcast.status === 'completed' && (
                <audio
                  controls
                  src={getAudioUrl(podcast.id)}
                  className="h-8"
                  preload="metadata"
                />
              )}
              {podcast.status === 'processing' && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              )}
              <button
                onClick={() => handleDelete(podcast.id, podcast.filename)}
                className="px-3 py-1.5 text-red-600 hover:bg-red-50 text-sm rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

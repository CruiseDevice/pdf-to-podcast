'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Podcast, PodcastStatus, listPodcasts, deletePodcast, getPodcastStatus, getAudioUrl } from '@/lib/api';

const PROGRESS_STEPS: { status: PodcastStatus; label: string; progress: number }[] = [
  { status: 'pending', label: 'Queued', progress: 0 },
  { status: 'extracting', label: 'Extracting', progress: 20 },
  { status: 'generating', label: 'Generating', progress: 60 },
  { status: 'converting', label: 'Converting', progress: 95 },
  { status: 'completed', label: 'Done', progress: 100 },
];

const getCurrentStepLabel = (status: PodcastStatus): string => {
  const step = PROGRESS_STEPS.find(s => s.status === status);
  return step?.label ?? status;
};

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
      (p) => !['completed', 'failed'].includes(p.status)
    );

    if (processingPodcasts.length === 0) return;

    const interval = setInterval(async () => {
      for (const podcast of processingPodcasts) {
        try {
          const status = await getPodcastStatus(podcast.id);
          setPodcasts((prev) =>
            prev.map((p) =>
              p.id === podcast.id
                ? {
                    ...p,
                    status: status.status as PodcastStatus,
                    progress: status.progress,
                    progress_message: status.progress_message,
                    error: status.error
                  }
                : p
            )
          );
          if (status.status === 'completed') {
            toast.success(`${podcast.filename} is ready!`);
          } else if (status.status === 'failed') {
            toast.error(`${podcast.filename} failed to process`);
          }
        } catch (error) {
          console.error('Failed to check status:', error);
        }
      }
    }, 2000);

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

  const getStatusBadge = (status: PodcastStatus) => {
    const styles: Record<PodcastStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      extracting: 'bg-blue-100 text-blue-800',
      generating: 'bg-purple-100 text-purple-800',
      converting: 'bg-indigo-100 text-indigo-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {getCurrentStepLabel(status)}
      </span>
    );
  };

  const ProgressBar = ({ podcast }: { podcast: Podcast }) => {
    if (podcast.status === 'completed' || podcast.status === 'failed') return null;

    const progress = parseInt(podcast.progress || '0', 10);
    const message = podcast.progress_message || 'Processing...';

    return (
      <div className="mt-3 w-full">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span className="text-blue-600 font-medium">{message}</span>
          <span className="font-medium">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-2">
          {PROGRESS_STEPS.slice(0, -1).map((step) => {
            const isActive = progress >= step.progress;
            const isCurrent = podcast.status === step.status;
            return (
              <div key={step.status} className="flex flex-col items-center">
                <div
                  className={`w-2.5 h-2.5 rounded-full mb-1 transition-colors ${
                    isActive ? 'bg-blue-600' : 'bg-gray-300'
                  } ${isCurrent ? 'ring-2 ring-blue-300 ring-offset-1' : ''}`}
                />
                <span
                  className={`text-xs transition-colors ${
                    isActive ? 'text-blue-600 font-medium' : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
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
            className="p-4 bg-white rounded-lg shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
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
                <button
                  onClick={() => handleDelete(podcast.id, podcast.filename)}
                  className="px-3 py-1.5 text-red-600 hover:bg-red-50 text-sm rounded-lg transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
            <ProgressBar podcast={podcast} />
          </div>
        ))}
      </div>
    </div>
  );
}

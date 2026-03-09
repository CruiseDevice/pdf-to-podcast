import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export type PodcastStatus = 'pending' | 'extracting' | 'generating' | 'converting' | 'completed' | 'failed';

export interface Podcast {
  id: string;
  filename: string;
  status: PodcastStatus;
  audio_url?: string;
  error?: string;
  created_at: string;
}

export interface UploadResponse {
  podcast_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  podcast_id: string;
  status: string;
  audio_url?: string;
  error?: string;
}

export const uploadPDF = async (
  file: File,
  title: string,
  description?: string,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  if (description) {
    formData.append('description', description);
  }

  const response = await api.post<UploadResponse>('/api/v1/podcasts', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });

  return response.data;
};

export const listPodcasts = async (): Promise<Podcast[]> => {
  const response = await api.get<Podcast[]>('/api/v1/podcasts');
  return response.data;
};

export const getPodcastStatus = async (podcastId: string): Promise<StatusResponse> => {
  const response = await api.get<StatusResponse>(`/api/v1/podcasts/${podcastId}/status`);
  return response.data;
};

export const deletePodcast = async (podcastId: string): Promise<void> => {
  await api.delete(`/api/v1/podcasts/${podcastId}`);
};

export const getAudioUrl = (podcastId: string): string => {
  return `${API_BASE_URL}/api/v1/podcasts/${podcastId}/audio`;
};

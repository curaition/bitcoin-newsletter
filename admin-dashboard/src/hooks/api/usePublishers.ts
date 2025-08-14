/**
 * Publishers API Hooks
 * 
 * React Query hooks for fetching and managing publisher data
 */

import { useQuery } from '@tanstack/react-query';
import type { Publisher } from '../../../../shared/types/api';
import { apiClient } from '@/services/api/client';
import { queryKeys } from '@/services/query/query-client';

// ============================================================================
// Publishers List Hook
// ============================================================================

export function usePublishers(options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;
  
  return useQuery({
    queryKey: queryKeys.publishers(),
    queryFn: () => apiClient.getPublishers(),
    enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes - publishers don't change often
    gcTime: 30 * 60 * 1000, // 30 minutes cache time
  });
}

// ============================================================================
// Publisher Lookup Hook
// ============================================================================

export function usePublisherLookup() {
  const { data: publishers = [] } = usePublishers();
  
  // Create a lookup map for quick publisher name resolution
  const publisherMap = publishers.reduce((map, publisher) => {
    map[publisher.id] = publisher;
    return map;
  }, {} as Record<number, Publisher>);
  
  return {
    publishers,
    publisherMap,
    getPublisherName: (publisherId: number | null): string => {
      if (!publisherId) return 'Unknown Publisher';
      const publisher = publisherMap[publisherId];
      return publisher?.name || `Publisher ${publisherId}`;
    },
    getPublisher: (publisherId: number | null): Publisher | null => {
      if (!publisherId) return null;
      return publisherMap[publisherId] || null;
    },
  };
}

// ============================================================================
// Publisher Cache Helpers
// ============================================================================

export function usePublisherCache() {
  const { data: publishers = [] } = usePublishers();
  
  return {
    // Get all publishers
    getAllPublishers: (): Publisher[] => publishers,
    
    // Find publisher by name
    findPublisherByName: (name: string): Publisher | undefined => {
      return publishers.find(p => 
        p.name.toLowerCase().includes(name.toLowerCase())
      );
    },
    
    // Get publishers for dropdown options
    getPublisherOptions: () => {
      return publishers.map(publisher => ({
        value: publisher.id.toString(),
        label: publisher.name,
      }));
    },
  };
}

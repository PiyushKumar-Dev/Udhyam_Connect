import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "./client";
import type {
  AuthUser,
  EntityGraphResponse,
  EntityDetail,
  EntityListResponse,
  EntitySummary,
  GraphOverviewResponse,
  MatchDecisionPayload,
  MatchPair,
  PincodeStatsResponse,
  StatsResponse
} from "../types";

interface EntityParams {
  status?: string;
  risk_level?: string;
  pincode?: string;
  page?: number;
  limit?: number;
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: async () => (await api.get<StatsResponse>("/api/stats")).data,
    staleTime: 30000  // Refetch after 30 seconds
  });
}

export function useEntities(params: EntityParams) {
  return useQuery({
    queryKey: ["entities", params],
    queryFn: async () =>
      (
        await api.get<EntityListResponse>("/api/entities", {
          params: {
            status: params.status,
            risk_level: params.risk_level,
            pincode: params.pincode,
            page: params.page ?? 1,
            limit: params.limit ?? 20
          }
        })
      ).data,
    staleTime: 30000  // Refetch after 30 seconds
  });
}

export function useEntity(ubid?: string) {
  return useQuery({
    queryKey: ["entity", ubid],
    enabled: Boolean(ubid),
    queryFn: async () => (await api.get<EntityDetail>(`/api/entities/${ubid}`)).data
  });
}

export function useSearch(term: string) {
  return useQuery({
    queryKey: ["search", term],
    enabled: term.trim().length > 1,
    queryFn: async () =>
      (await api.get<EntitySummary[]>("/api/search", { params: { q: term } })).data
  });
}

export function usePendingMatches() {
  return useQuery({
    queryKey: ["matches", "pending"],
    queryFn: async () => (await api.get<MatchPair[]>("/api/matches/pending")).data
  });
}

export function useDecideMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      matchId,
      payload
    }: {
      matchId: string;
      payload: MatchDecisionPayload;
    }) => (await api.post(`/api/matches/${matchId}/decide`, payload)).data,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["matches", "pending"] }),
        queryClient.invalidateQueries({ queryKey: ["entities"] }),
        queryClient.invalidateQueries({ queryKey: ["stats"] })
      ]);
    }
  });
}

export function useGraphOverview() {
  return useQuery({
    queryKey: ["graph", "overview"],
    queryFn: async () => (await api.get<GraphOverviewResponse>("/api/graph/overview")).data
  });
}

export function useEntityGraph(ubid?: string) {
  return useQuery({
    queryKey: ["graph", "entity", ubid],
    enabled: Boolean(ubid),
    queryFn: async () => (await api.get<EntityGraphResponse>(`/api/graph/entity/${ubid}`)).data
  });
}

export function usePincodeStats(q?: string) {
  return useQuery({
    queryKey: ["stats", "pincodes", q],
    queryFn: async () =>
      (await api.get<PincodeStatsResponse>("/api/stats/pincodes", { params: { q } })).data,
    staleTime: 30000
  });
}

export function useAuthMe() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => (await api.get<AuthUser>("/api/auth/me")).data
  });
}

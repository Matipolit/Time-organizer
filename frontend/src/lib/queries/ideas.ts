import {
  createQuery,
  createMutation,
  useQueryClient,
} from "@tanstack/svelte-query";
import { api, type Idea, type IdeaUpdate, TaskType } from "../api";

const keys = {
  all: ["ideas"] as const,
  lists: () => [...keys.all, "list"] as const,
  details: () => [...keys.all, "detail"] as const,
  detail: (id: number) => [...keys.details(), id] as const,
};

// Task keys for invalidation after conversion
const taskKeys = {
  all: ["tasks"] as const,
  lists: () => [...taskKeys.all, "list"] as const,
};

export function useIdeas() {
  return createQuery(() => ({
    queryKey: keys.lists(),
    queryFn: () => api.getIdeas(),
    staleTime: 60000, // 1 minute
  }));
}

export function useIdeaMutation() {
  const client = useQueryClient();

  return {
    create: createMutation(() => ({
      mutationFn: api.createIdea,
      onSuccess: () => {
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    update: createMutation(() => ({
      mutationFn: ({ id, updates }: { id: number; updates: IdeaUpdate }) =>
        api.updateIdea(id, updates),
      onSuccess: () => {
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    delete: createMutation(() => ({
      mutationFn: api.deleteIdea,
      onSuccess: () => {
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    convert: createMutation(() => ({
      mutationFn: ({ id, taskType }: { id: number; taskType?: TaskType }) =>
        api.convertIdeaToTask(id, taskType),
      onSuccess: () => {
        // Invalidate both ideas and tasks
        client.invalidateQueries({ queryKey: keys.lists() });
        client.invalidateQueries({ queryKey: taskKeys.lists() });
      },
    })),
  };
}

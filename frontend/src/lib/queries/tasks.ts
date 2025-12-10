import {
  createQuery,
  createMutation,
  useQueryClient,
} from "@tanstack/svelte-query";
import { api, type Task } from "../api";
import type { TaskFilters } from "../stores/taskFilters";

// 1. The Key Factory (Prevents typo bugs in cache keys)
// The key includes the entire filter object - TanStack Query will automatically
// handle cache invalidation when filters change
const keys = {
  all: ["tasks"] as const,
  lists: () => [...keys.all, "list"] as const,
  list: (filters: TaskFilters) => [...keys.lists(), filters] as const,
  details: () => [...keys.all, "detail"] as const,
  detail: (id: number) => [...keys.details(), id] as const,
};

// 2. The Query Hook (GET)
// Now accepts a full filters object instead of just a boolean
export function useTasks(filters: TaskFilters = {}) {
  return createQuery(() => ({
    queryKey: keys.list(filters),
    queryFn: () => api.getTasks(filters),
    // Optional: Keep data fresh
    staleTime: 30000, // 30 seconds
  }));
}

// 3. The Mutation Hook (POST/PATCH/DELETE)
export function useTaskMutation() {
  const client = useQueryClient();

  return {
    create: createMutation(() => ({
      mutationFn: api.createTask,
      onSuccess: () => {
        // Invalidate the cache so the list updates automatically
        // This invalidates ALL task lists regardless of filters
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    complete: createMutation(() => ({
      mutationFn: api.completeTask,
      onMutate: async (taskId) => {
        // OPTIONAL: Optimistic Update Logic (Instant UI feedback)
        // 1. Cancel outgoing fetches
        await client.cancelQueries({ queryKey: keys.lists() });

        // 2. Snapshot previous value
        const previousTasks = client.getQueryData(keys.lists());

        // 3. Optimistically update all cached lists
        client.setQueriesData(
          { queryKey: keys.lists() },
          (old: Task[] | undefined) => {
            if (!old) return old;
            return old.filter((t) => t.id !== taskId); // Remove the task instantly
          },
        );

        return { previousTasks };
      },
      onError: (err, taskId, context) => {
        // If API fails, roll back to the snapshot
        if (context) {
          client.setQueryData(keys.lists(), context.previousTasks);
        }
      },
      onSettled: () => {
        // Always refetch after error or success to ensure sync
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    uncomplete: createMutation(() => ({
      mutationFn: api.uncompleteTask,
      onSuccess: () => {
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    delete: createMutation(() => ({
      mutationFn: api.deleteTask,
      onSuccess: () => {
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),

    update: createMutation(() => ({
      mutationFn: ({ id, updates }: { id: number; updates: Partial<Task> }) =>
        api.updateTask(id, updates),
      onSuccess: () => {
        client.invalidateQueries({ queryKey: keys.lists() });
      },
    })),
  };
}

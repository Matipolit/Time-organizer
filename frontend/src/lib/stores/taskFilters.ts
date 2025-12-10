import { writable, derived } from "svelte/store";
import { TaskType, TaskStatus } from "../api";

export interface TaskFilters {
  // Status filters
  status?: TaskStatus[];

  // Type filters
  taskTypes?: TaskType[];

  // Date filters
  dateRange?: {
    start?: string; // ISO date string
    end?: string;   // ISO date string
  };
  onlyToday?: boolean;
  onlyOverdue?: boolean;

  // Text search
  searchQuery?: string;

  // Effort filters
  efforts?: string[];

  // Other filters
  hasDeadline?: boolean;
  parentId?: number; // For filtering subtasks
}

// Default empty filters
const defaultFilters: TaskFilters = {
  status: undefined,
  taskTypes: undefined,
  dateRange: undefined,
  onlyToday: false,
  onlyOverdue: false,
  searchQuery: undefined,
  efforts: undefined,
  hasDeadline: undefined,
  parentId: undefined,
};

function createTaskFiltersStore() {
  const { subscribe, set, update } = writable<TaskFilters>(defaultFilters);

  return {
    subscribe,

    // Set individual filter
    setFilter: <K extends keyof TaskFilters>(key: K, value: TaskFilters[K]) => {
      update(filters => ({ ...filters, [key]: value }));
    },

    // Toggle a status filter
    toggleStatus: (status: TaskStatus) => {
      update(filters => {
        const current = filters.status || [];
        const newStatus = current.includes(status)
          ? current.filter(s => s !== status)
          : [...current, status];

        return {
          ...filters,
          status: newStatus.length > 0 ? newStatus : undefined,
        };
      });
    },

    // Toggle a task type filter
    toggleTaskType: (taskType: TaskType) => {
      update(filters => {
        const current = filters.taskTypes || [];
        const newTypes = current.includes(taskType)
          ? current.filter(t => t !== taskType)
          : [...current, taskType];

        return {
          ...filters,
          taskTypes: newTypes.length > 0 ? newTypes : undefined,
        };
      });
    },

    // Set date range
    setDateRange: (start?: string, end?: string) => {
      update(filters => ({
        ...filters,
        dateRange: start || end ? { start, end } : undefined,
      }));
    },

    // Quick filters
    showOnlyToday: () => {
      update(filters => ({ ...filters, onlyToday: true, onlyOverdue: false, dateRange: undefined }));
    },

    showOnlyOverdue: () => {
      update(filters => ({ ...filters, onlyOverdue: true, onlyToday: false, dateRange: undefined }));
    },

    showAll: () => {
      update(filters => ({ ...filters, onlyToday: false, onlyOverdue: false, dateRange: undefined }));
    },

    // Reset all filters
    reset: () => set(defaultFilters),

    // Set all filters at once
    setFilters: (filters: TaskFilters) => set(filters),
  };
}

export const taskFilters = createTaskFiltersStore();

// Derived store: Check if any filters are active
export const hasActiveFilters = derived(
  taskFilters,
  ($filters) => {
    return (
      ($filters.status && $filters.status.length > 0) ||
      ($filters.taskTypes && $filters.taskTypes.length > 0) ||
      $filters.onlyToday ||
      $filters.onlyOverdue ||
      ($filters.dateRange && ($filters.dateRange.start || $filters.dateRange.end)) ||
      ($filters.searchQuery && $filters.searchQuery.length > 0) ||
      ($filters.efforts && $filters.efforts.length > 0) ||
      $filters.hasDeadline !== undefined ||
      $filters.parentId !== undefined
    );
  }
);

// Helper to convert filters to URL query params (for API calls)
export function filtersToQueryParams(filters: TaskFilters): string {
  const params = new URLSearchParams();

  if (filters.status && filters.status.length > 0) {
    filters.status.forEach(s => params.append("status", s));
  }

  if (filters.taskTypes && filters.taskTypes.length > 0) {
    filters.taskTypes.forEach(t => params.append("task_type", t));
  }

  if (filters.onlyToday) {
    params.append("only_today", "true");
  }

  if (filters.onlyOverdue) {
    params.append("only_overdue", "true");
  }

  if (filters.dateRange?.start) {
    params.append("start_date", filters.dateRange.start);
  }

  if (filters.dateRange?.end) {
    params.append("end_date", filters.dateRange.end);
  }

  if (filters.searchQuery) {
    params.append("search", filters.searchQuery);
  }

  if (filters.efforts && filters.efforts.length > 0) {
    filters.efforts.forEach(e => params.append("effort", e));
  }

  if (filters.hasDeadline !== undefined) {
    params.append("has_deadline", String(filters.hasDeadline));
  }

  if (filters.parentId !== undefined) {
    params.append("parent_id", String(filters.parentId));
  }

  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

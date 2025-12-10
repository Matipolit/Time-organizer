import type { TaskFilters } from "./stores/taskFilters";
import { filtersToQueryParams } from "./stores/taskFilters";

export enum TaskType {
  DEADLINE = "deadline",
  CHORE = "chore",
  STREAK = "streak",
}

export enum TaskStatus {
  TODO = "todo",
  DONE = "done",
}

export enum EffortLevel {
  S = "S", // < 15 mins
  M = "M", // ~ 1 hour
  L = "L", // ~ 2-3 hours
  XL = "XL", // Too big
}

export interface Task {
  id?: number; // Optional because new tasks don't have an ID yet
  title: string;
  description?: string;
  task_type: TaskType;
  status: TaskStatus;

  // The "Do Date" (ISO 8601 String)
  scheduled_date?: string;
  effort?: EffortLevel;

  // Deadline Specifics
  parent_id?: number;
  deadline?: string;

  // Chore Specifics
  recurrence_interval_days?: number;

  // Streak Specifics
  current_streak?: number;
  best_streak?: number;

  // Nested tasks
  children?: Task[];

  // Metadata
  created_at?: string;
  last_completed_at?: string;
}

const API_BASE = "/timely/api"; // proxied by vite

async function request<T>(
  endpoint: string,
  method: "GET" | "POST" | "PATCH" | "DELETE" = "GET",
  body?: unknown,
): Promise<T> {
  const options: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status}: ${errorText}`);
  }

  // Handle empty responses (like DELETE)
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// API methods

export const api = {
  // Fetch tasks with optional filters
  getTasks: async (filters: TaskFilters = {}) => {
    const queryString = filtersToQueryParams(filters);
    return request<Task[]>(`/tasks/${queryString}`);
  },

  // Create a new task
  createTask: async (task: Partial<Task>) => {
    return request<Task>("/tasks/", "POST", task);
  },

  // The "Magic" Complete (Handles streaks/recurrence on backend)
  completeTask: async (taskId: number) => {
    return request<Task>(`/tasks/${taskId}/done`, "PATCH");
  },

  uncompleteTask: async (taskId: number) => {
    return request<Task>(`/tasks/${taskId}/undone`, "PATCH");
  },

  // Update a task
  updateTask: async (taskId: number, updates: Partial<Task>) => {
    return request<Task>(`/tasks/${taskId}`, "PATCH", updates);
  },

  // Delete
  deleteTask: async (taskId: number) => {
    return request<{ ok: boolean }>(`/tasks/${taskId}`, "DELETE");
  },
};

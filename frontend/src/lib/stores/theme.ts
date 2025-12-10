import { writable } from "svelte/store";

// Define the available themes for TypeScript safety
export type Theme = "light" | "dark" | "forest" | "cyberpunk";

// Export array of all themes as single source of truth
export const THEMES: readonly Theme[] = [
  "light",
  "dark",
  "forest",
  "cyberpunk",
] as const;

function createThemeStore() {
  // 1. Check local storage or system preference on load
  const storedTheme = localStorage.getItem("app-theme") as Theme | null;
  const initialTheme = storedTheme || "light";

  const { subscribe, set } = writable<Theme>(initialTheme);

  // Helper function to apply theme to DOM
  const applyThemeToDOM = (theme: Theme) => {
    const root = document.documentElement;

    // Reset classes
    root.classList.remove("dark");
    root.removeAttribute("data-theme");

    if (theme === "dark") {
      root.classList.add("dark");
    } else if (theme !== "light") {
      root.setAttribute("data-theme", theme);
    }
  };

  // Initialize theme immediately on load
  if (typeof document !== "undefined") {
    applyThemeToDOM(initialTheme);
  }

  return {
    subscribe,
    set: (theme: Theme) => {
      // 2. Update the Store
      set(theme);

      // 3. Update the DOM (The actual visual switch)
      applyThemeToDOM(theme);

      // 4. Save preference
      localStorage.setItem("app-theme", theme);
    },
  };
}

export const theme = createThemeStore();

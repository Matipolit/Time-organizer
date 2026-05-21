import { writable } from "svelte/store";

export type Palette = "default" | "forest" | "gruvbox" | "cyberpunk";
export type ColorMode = "system" | "light" | "dark";

export const PALETTES: readonly Palette[] = [
  "default",
  "forest",
  "gruvbox",
  "cyberpunk",
] as const;
export const MODES: readonly ColorMode[] = ["system", "light", "dark"] as const;

function createThemeStore() {
  const storedPalette = localStorage.getItem("app-palette") as Palette | null;
  const storedMode = localStorage.getItem("app-mode") as ColorMode | null;

  const initialPalette: Palette = storedPalette || "default";
  const initialMode: ColorMode = storedMode || "system";

  const palette = writable<Palette>(initialPalette);
  const mode = writable<ColorMode>(initialMode);

  const applyToDOM = (p: Palette, m: ColorMode) => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;

    // 1. Handle Palette
    root.setAttribute("data-palette", p);

    // 2. Handle Mode
    root.classList.remove("light", "dark");
    if (m === "light") {
      root.classList.add("light");
    } else if (m === "dark") {
      root.classList.add("dark");
    }
    // If "system", we remove both and let CSS media queries handle it
  };

  // Initialize
  if (typeof document !== "undefined") {
    applyToDOM(initialPalette, initialMode);
  }

  return {
    palette: {
      subscribe: palette.subscribe,
      set: (newPalette: Palette) => {
        palette.set(newPalette);
        let currentMode: ColorMode = "system";
        mode.subscribe((m) => (currentMode = m))();
        applyToDOM(newPalette, currentMode);
        localStorage.setItem("app-palette", newPalette);
      },
    },
    mode: {
      subscribe: mode.subscribe,
      set: (newMode: ColorMode) => {
        mode.set(newMode);
        let currentPalette: Palette = "default";
        palette.subscribe((p) => (currentPalette = p))();
        applyToDOM(currentPalette, newMode);
        localStorage.setItem("app-mode", newMode);
      },
    },
  };
}

export const theme = createThemeStore();

<script lang="ts">
    import {
        theme,
        PALETTES,
        MODES,
        type Palette,
        type ColorMode,
    } from "../lib/stores/theme";
    import {
        Check,
        Trash,
        Monitor,
        Palette as PaletteIcon,
        Sun,
        Moon,
    } from "lucide-svelte";
    import Button from "./Button.svelte";

    const paletteLabels: Record<Palette, string> = {
        default: "Domyślny",
        forest: "Las",
        gruvbox: "Gruvbox",
        cyberpunk: "Cyberpunk",
    };

    const modeIcons: Record<ColorMode, any> = {
        system: Monitor,
        light: Sun,
        dark: Moon,
    };

    const modeLabels: Record<ColorMode, string> = {
        system: "Systemowy",
        light: "Jasny",
        dark: "Ciemny",
    };

    const { palette: paletteStore, mode: modeStore } = theme;
</script>

<div class="h-full overflow-y-auto max-w-md mx-auto space-y-10 p-4">
    <section class="space-y-4">
        <h2 class="text-2xl font-bold flex items-center gap-2">
            <PaletteIcon size={24} /> Paleta kolorów
        </h2>
        <p class="text-muted-foreground">
            Wybierz główny zestaw kolorów aplikacji.
        </p>

        <div class="grid grid-cols-2 gap-3">
            {#each PALETTES as p}
                <Button
                    variant={$paletteStore === p ? "primary" : "outline"}
                    onclick={() => paletteStore.set(p)}
                    class="justify-start gap-2"
                >
                    {paletteLabels[p]}
                </Button>
            {/each}
        </div>
    </section>

    <section class="space-y-4">
        <h2 class="text-2xl font-bold flex items-center gap-2">
            <Monitor size={24} /> Tryb wyświetlania
        </h2>
        <p class="text-muted-foreground">
            Wymuś tryb jasny/ciemny lub synchronizuj z systemem.
        </p>

        <div class="grid grid-cols-3 gap-3">
            {#each MODES as m}
                {@const Icon = modeIcons[m]}
                <Button
                    variant={$modeStore === m ? "primary" : "outline"}
                    onclick={() => modeStore.set(m)}
                    class="flex-col gap-2 h-auto py-4"
                >
                    <Icon size={20} />
                    <span class="text-xs">{modeLabels[m]}</span>
                </Button>
            {/each}
        </div>
    </section>

    <section class="pt-4 border-t border-muted">
        <p class="text-sm font-medium mb-4">Podgląd:</p>
        <div
            class="flex flex-col border p-4 gap-3 rounded-xl bg-card text-card-foreground shadow-sm"
        >
            <div class="flex items-center gap-2">
                <div
                    class="w-8 h-8 rounded-full bg-primary flex items-center justify-center"
                >
                    <Check class="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                    <p class="font-bold">Przykład Zadania</p>
                    <p class="text-xs text-muted-foreground">Dzisiaj, 14:00</p>
                </div>
            </div>

            <p class="text-sm text-foreground/80">
                To jest podgląd jak będą wyglądać kolory w wybranej
                konfiguracji.
            </p>

            <div class="flex gap-2">
                <Button variant="primary" class="text-xs py-1 h-8"
                    >Zrób to</Button
                >
                <Button variant="outline" class="text-xs py-1 h-8"
                    >Później</Button
                >
                <Button variant="destructive" class="text-xs py-1 h-8 px-2"
                    ><Trash size={14} /></Button
                >
            </div>
        </div>
    </section>
</div>

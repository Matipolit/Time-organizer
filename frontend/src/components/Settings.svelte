<script lang="ts">
    import { theme, THEMES, type Theme } from "../lib/stores/theme";
    import { Check, Trash } from "lucide-svelte";
    import { fade } from "svelte/transition";
    import Button from "./Button.svelte";

    // Helper to make theme names pretty (e.g. "cyberpunk" -> "Cyberpunk")
    const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
</script>

<div class="max-w-md mx-auto space-y-8 p-4">
    <section class="space-y-4">
        <h2 class="text-2xl font-bold">Wygląd</h2>
        <p class="text-muted-foreground">Wybierz który motyw ci odpowiada.</p>

        <div class="grid grid-cols-2 gap-4">
            {#each THEMES as t}
                <Button variant="primary" onclick={() => theme.set(t)}>
                    {capitalize(t)}
                </Button>
            {/each}
        </div>
        <div>
            <p>Podgląd:</p>
            <div
                class="flex flex-col space-x-2 border p-4 gap-1 rounded-xl bg-card text-card-foreground"
            >
                <div>
                    <Check class="w-6 h-6 text-primary" />
                    <p class="text-xl">Tytuł</p>
                </div>
                <p class="text-muted-foreground">Podtytuł</p>
                <div class="flex gap-2">
                    <Button variant="primary">Zaznacz</Button>
                    <Button variant="outline">Odśwież</Button>
                    <Button variant="destructive"><Trash />Usuń</Button>
                </div>
            </div>
        </div>
    </section>
</div>

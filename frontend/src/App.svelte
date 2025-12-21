<script lang="ts">
    import { QueryClient, QueryClientProvider } from "@tanstack/svelte-query";
    import Interface from "./components/Interface.svelte";
    import { ArrowLeft, SettingsIcon } from "lucide-svelte";
    import Settings from "./components/Settings.svelte";
    import Button from "./components/Button.svelte";

    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 1000 * 60 * 5, // Data is fresh for 5 minutes
                refetchOnWindowFocus: true,
            },
        },
    });

    type Page = "main" | "settings";

    // Export array of all themes as single source of truth
    export const PAGES: readonly Page[] = ["main", "settings"] as const;

    let page = $state("main");
</script>

<main
    class="min-h-screen bg-background text-foreground transition-colors duration-300"
>
    <header class="flex justify-between items-center w-full gap-4 bg-muted p-4">
        {#if page !== "main"}
            <Button variant="ghost" onclick={() => (page = "main")}>
                <ArrowLeft />
            </Button>
        {:else}
            <span></span>
        {/if}
        <h1 class="text-xl font-bold">Organizator Zadań</h1>
        {#if page !== "settings"}
            <Button variant="ghost" onclick={() => (page = "settings")}>
                <SettingsIcon />
            </Button>
        {:else}
            <span></span>
        {/if}
    </header>
    <div class="p-2">
        <QueryClientProvider client={queryClient}>
            {#if page === "main"}
                <Interface />
            {:else if page === "settings"}
                <Settings />
            {/if}
        </QueryClientProvider>
    </div>
</main>

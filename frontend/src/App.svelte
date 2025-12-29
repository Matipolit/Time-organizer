<script lang="ts">
    import { QueryClient, QueryClientProvider } from "@tanstack/svelte-query";
    import Interface from "./components/Interface.svelte";
    import Login from "./components/Login.svelte";
    import { ArrowLeft, SettingsIcon, LogOut } from "lucide-svelte";
    import Settings from "./components/Settings.svelte";
    import Button from "./components/Button.svelte";
    import { api } from "./lib/api";

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
    let isAuthenticated = $state(false);
    let loading = $state(true);

    // Check if user is already logged in
    async function checkAuth() {
        try {
            const token =
                typeof window !== "undefined"
                    ? localStorage.getItem("auth_token")
                    : null;
            if (token) {
                await api.verifyToken();
                isAuthenticated = true;
            }
        } catch (err) {
            isAuthenticated = false;
            localStorage.removeItem("auth_token");
        } finally {
            loading = false;
        }
    }

    // Listen for login events
    if (typeof window !== "undefined") {
        window.addEventListener("login-success", () => {
            isAuthenticated = true;
            page = "main";
        });
    }

    // Check auth on mount
    if (typeof window !== "undefined") {
        checkAuth();
    }

    function handleLogout() {
        api.logout();
        isAuthenticated = false;
        page = "main";
    }
</script>

{#if loading}
    <div class="min-h-screen flex items-center justify-center bg-background">
        <p class="text-muted-foreground">Loading...</p>
    </div>
{:else if !isAuthenticated}
    <Login />
{:else}
    <main
        class="min-h-screen bg-background text-foreground transition-colors duration-300"
    >
        <header
            class="flex justify-between items-center w-full gap-4 bg-muted p-4"
        >
            <div class="flex items-center gap-2">
                {#if page !== "main"}
                    <Button variant="ghost" onclick={() => (page = "main")}>
                        <ArrowLeft />
                    </Button>
                {/if}
            </div>
            <h1 class="text-xl font-bold">Organizator Zadań</h1>
            <div class="flex items-center gap-2">
                {#if page !== "settings"}
                    <Button variant="ghost" onclick={() => (page = "settings")}>
                        <SettingsIcon />
                    </Button>
                {/if}
                <Button variant="ghost" onclick={handleLogout}>
                    <LogOut />
                </Button>
            </div>
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
{/if}

<script lang="ts">
    import { api } from "../lib/api";
    import Button from "./Button.svelte";

    let username = $state("");
    let password = $state("");
    let error = $state("");
    let loading = $state(false);

    async function handleLogin() {
        error = "";
        loading = true;
        try {
            await api.login(username, password);
            // Dispatch event to parent to show main interface
            window.dispatchEvent(new CustomEvent("login-success"));
        } catch (err) {
            error =
                err instanceof Error
                    ? err.message
                    : "Login failed. Please try again.";
        } finally {
            loading = false;
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter") {
            handleLogin();
        }
    }
</script>

<div
    class="min-h-screen flex items-center justify-center bg-background text-foreground"
>
    <div
        class="w-full max-w-md p-8 rounded-lg border border-border bg-card shadow-lg"
    >
        <h1 class="text-3xl font-bold text-center mb-2">Organizator Zadań</h1>
        <p class="text-center text-muted-foreground mb-8">Zaloguj się</p>

        <form onsubmit={(e) => e.preventDefault()} class="space-y-4">
            <div>
                <label for="username" class="block text-sm font-medium mb-2">
                    Login
                </label>
                <input
                    type="text"
                    id="username"
                    bind:value={username}
                    onkeydown={handleKeydown}
                    disabled={loading}
                    class="w-full px-3 py-2 rounded border border-input bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                    placeholder="Wpisz login"
                />
            </div>

            <div>
                <label for="password" class="block text-sm font-medium mb-2">
                    Hasło
                </label>
                <input
                    type="password"
                    id="password"
                    bind:value={password}
                    onkeydown={handleKeydown}
                    disabled={loading}
                    class="w-full px-3 py-2 rounded border border-input bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                    placeholder="Wpisz hasło"
                />
            </div>

            {#if error}
                <div
                    class="p-3 rounded bg-destructive/10 text-destructive text-sm"
                >
                    {error}
                </div>
            {/if}

            <Button
                onclick={handleLogin}
                disabled={loading || !username || !password}
                class="w-full"
            >
                {loading ? "Logging in..." : "Login"}
            </Button>
        </form>
    </div>
</div>

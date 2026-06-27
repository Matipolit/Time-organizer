<script lang="ts">
    import { Lightbulb, Plus, Loader2 } from "lucide-svelte";
    import { useIdeas, useIdeaMutation } from "../lib/queries/ideas";
    import IdeaCard from "./IdeaCard.svelte";
    import type { Idea } from "../lib/api";
    import Button from "./Button.svelte";

    const ideasQuery = useIdeas();
    const mutations = useIdeaMutation();

    let quickAddTitle = $state("");
    let editingIdea = $state<Idea | null>(null);

    const ideas = $derived(ideasQuery.data ?? []);
    const isLoading = $derived(ideasQuery.isLoading);
    const isError = $derived(ideasQuery.isError);

    async function handleQuickAdd(e: Event) {
        e.preventDefault();
        if (!quickAddTitle.trim()) return;

        mutations.create.mutate(
            { title: quickAddTitle.trim() },
            {
                onSuccess: () => {
                    quickAddTitle = "";
                },
            },
        );
    }

    function handleEdit(idea: Idea) {
        editingIdea = { ...idea };
    }

    function closeEdit() {
        editingIdea = null;
    }

    function saveEdit() {
        if (!editingIdea || !editingIdea.id) return;
        mutations.update.mutate(
            {
                id: editingIdea.id,
                updates: {
                    title: editingIdea.title,
                    description: editingIdea.description,
                },
            },
            {
                onSuccess: closeEdit,
            },
        );
    }
</script>

<div class="h-full overflow-y-auto space-y-6 max-w-4xl mx-auto pb-10 pr-2">
    <div class="flex items-center gap-3 mb-2">
        <Lightbulb class="text-primary" size={28} />
        <h2 class="text-2xl font-bold">Skrzynka Pomysłów</h2>
    </div>

    <!-- Quick Add -->
    <form
        onsubmit={handleQuickAdd}
        class="flex gap-2 p-1 bg-muted rounded-xl border-2 border-transparent focus-within:border-primary transition-all"
    >
        <input
            bind:value={quickAddTitle}
            placeholder="Wpisz nowy pomysł i naciśnij Enter..."
            class="flex-1 bg-transparent px-4 py-2 outline-none text-lg"
            disabled={mutations.create.isPending}
        />
        <Button
            type="submit"
            variant="primary"
            disabled={!quickAddTitle.trim() || mutations.create.isPending}
        >
            {#if mutations.create.isPending}
                <Loader2 class="animate-spin" size={20} />
            {:else}
                <Plus size={20} />
            {/if}
        </Button>
    </form>

    {#if isLoading}
        <div class="flex justify-center py-10">
            <Loader2 class="animate-spin text-primary" size={40} />
        </div>
    {:else if isError}
        <p class="text-destructive text-center py-10">
            Błąd podczas ładowania pomysłów.
        </p>
    {:else if ideas.length === 0}
        <div
            class="text-center py-20 bg-muted/30 rounded-2xl border-2 border-dashed border-muted"
        >
            <Lightbulb class="mx-auto mb-4 text-muted-foreground" size={48} />
            <p class="text-xl text-muted-foreground">
                Nie masz jeszcze żadnych pomysłów.
            </p>
            <p class="text-muted-foreground">
                Zapisz coś, co chodzi Ci po głowie!
            </p>
        </div>
    {:else}
        <div class="grid gap-4">
            {#each ideas as idea (idea.id)}
                <IdeaCard {idea} onEdit={handleEdit} />
            {/each}
        </div>
    {/if}
</div>

<!-- Simple Edit Modal -->
{#if editingIdea}
    <div
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onclick={closeEdit}
        role="button"
        tabindex="-1"
        onkeydown={(e) => e.key === "Escape" && closeEdit()}
    >
        <div
            class="bg-card rounded-lg shadow-xl max-w-xl w-full p-6"
            onclick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            tabindex="0"
            onkeydown={(e) => e.stopPropagation()}
        >
            <h2 class="text-xl font-bold mb-4">Edytuj pomysł</h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1" for="title"
                        >Tytuł</label
                    >
                    <input
                        id="title"
                        bind:value={editingIdea.title}
                        class="w-full p-2 rounded border bg-background"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1" for="desc"
                        >Opis</label
                    >
                    <textarea
                        id="desc"
                        bind:value={editingIdea.description}
                        class="w-full p-2 rounded border bg-background min-h-[100px]"
                    ></textarea>
                </div>
                <div class="flex justify-end gap-2 mt-6">
                    <Button variant="outline" onclick={closeEdit}>Anuluj</Button
                    >
                    <Button
                        variant="primary"
                        onclick={saveEdit}
                        disabled={mutations.update.isPending}
                    >
                        Zapisz zmiany
                    </Button>
                </div>
            </div>
        </div>
    </div>
{/if}

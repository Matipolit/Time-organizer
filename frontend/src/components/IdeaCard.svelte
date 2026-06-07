<script lang="ts">
    import { Pencil, Trash2, Zap, Calendar } from "lucide-svelte";
    import type { Idea } from "../lib/api";
    import { useIdeaMutation } from "../lib/queries/ideas";

    interface Props {
        idea: Idea;
        onEdit: (idea: Idea) => void;
    }

    let { idea, onEdit }: Props = $props();

    const mutations = useIdeaMutation();

    function handleDelete(e: MouseEvent) {
        e.stopPropagation();
        if (confirm(`Czy na pewno chcesz usunąć pomysł "${idea.title}"?`)) {
            mutations.delete.mutate(idea.id!);
        }
    }

    function handleEdit(e: MouseEvent) {
        e.stopPropagation();
        onEdit(idea);
    }

    function handleConvert(e: MouseEvent) {
        e.stopPropagation();
        mutations.convert.mutate({ id: idea.id! });
    }

    const formattedDate = $derived(
        idea.created_at ? new Date(idea.created_at).toLocaleDateString() : "",
    );

    function handleDescriptionClick(e: MouseEvent) {
        if ((e.target as HTMLElement).tagName === "A") {
            e.stopPropagation();
        }
    }
</script>

<div
    class="p-4 border-2 border-muted-foreground/25 rounded-lg hover:shadow-md transition-shadow bg-card relative group"
>
    <!-- Action Buttons -->
    <div
        class="absolute top-2 right-2 flex gap-1
           opacity-100 lg:opacity-0 lg:group-hover:opacity-100
           transition-opacity"
    >
        <button
            onclick={handleConvert}
            class="p-3 lg:p-2 bg-background hover:bg-primary hover:text-primary-foreground rounded-lg transition-colors"
            aria-label="Konwertuj na zadanie"
            title="Konwertuj na zadanie"
        >
            <Zap size={16} />
        </button>
        <button
            onclick={handleEdit}
            class="p-3 lg:p-2 bg-background hover:bg-muted rounded-lg transition-colors"
            aria-label="Edytuj pomysł"
            title="Edytuj pomysł"
        >
            <Pencil size={16} />
        </button>
        <button
            onclick={handleDelete}
            class="p-3 lg:p-2 bg-background hover:bg-destructive hover:text-destructive-foreground rounded-lg transition-colors"
            aria-label="Usuń pomysł"
            title="Usuń pomysł"
        >
            <Trash2 size={16} />
        </button>
    </div>

    <h3 class="text-md font-semibold pr-32">
        {idea.title}
    </h3>
    {#if idea.description_html}
        <div
            class="text-foreground/80 mt-2 prose prose-sm max-w-none"
            onclick={handleDescriptionClick}
            onkeydown={(e) => e.key === "Enter" && handleDescriptionClick}
            role="button"
            tabindex="0"
        >
            {@html idea.description_html}
        </div>
    {:else if idea.description}
        <p class="text-foreground/80 mt-2">
            {idea.description}
        </p>
    {/if}
    {#if formattedDate}
        <span
            class="text-sm text-muted-foreground mt-2 flex gap-1 items-center"
        >
            <Calendar size={14} class="text-muted-foreground" />
            {formattedDate}
        </span>
    {/if}
</div>

<script lang="ts">
    import { CalendarIcon, ListIcon, Plus } from "lucide-svelte";
    import Button from "./Button.svelte";
    import ListView from "./ListView.svelte";
    import CalendarView from "./CalendarView.svelte";
    import AddTask from "./AddTask.svelte";

    const VIEW_MODES = ["list", "calendar"] as const;

    let viewMode: (typeof VIEW_MODES)[number] = $state("list");
    let showAddTask = $state(false);
</script>

<div class="">
    <div class="mb-2 flex justify-between items-center">
        <div class="flex gap-2">
            <Button
                onclick={() => {
                    viewMode = "list";
                }}
                variant="outline"
                selected={viewMode == "list"}><ListIcon />Lista</Button
            >
            <Button
                onclick={() => {
                    viewMode = "calendar";
                }}
                variant="outline"
                selected={viewMode == "calendar"}
                ><CalendarIcon />Kalendarz</Button
            >
        </div>
        <Button
            onclick={() => {
                showAddTask = true;
            }}
            variant="primary"
        >
            <Plus />
        </Button>
    </div>
    {#if viewMode == "list"}
        <ListView />
    {:else if viewMode == "calendar"}
        <CalendarView />
    {/if}
</div>

{#if showAddTask}
    <AddTask
        onClose={() => {
            showAddTask = false;
        }}
    />
{/if}

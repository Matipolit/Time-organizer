<script lang="ts">
    import {
        CalendarIcon,
        LayoutDashboardIcon,
        ListIcon,
        Plus,
        Lightbulb,
    } from "lucide-svelte";
    import Button from "./Button.svelte";
    import Dashboard from "./Dashboard.svelte";
    import CalendarView from "./CalendarView.svelte";
    import IdeasView from "./IdeasView.svelte";
    import AddTask from "./AddTask.svelte";

    const VIEW_MODES = ["dashboard", "calendar", "ideas"] as const;

    let viewMode: (typeof VIEW_MODES)[number] = $state("dashboard");
    let showAddTask = $state(false);
</script>

<div class="">
    <div class="mb-2 flex justify-between items-center">
        <div
            class="flex gap-2 pt-3 pb-3 justify-between w-full border-solid border-b-2 border-muted-foreground/50"
        >
            <div class="flex gap-2">
                <Button
                    onclick={() => {
                        viewMode = "dashboard";
                    }}
                    variant="outline"
                    selected={viewMode == "dashboard"}
                    ><LayoutDashboardIcon />Dashboard</Button
                >
                <Button
                    onclick={() => {
                        viewMode = "calendar";
                    }}
                    variant="outline"
                    selected={viewMode == "calendar"}
                    ><CalendarIcon />Kalendarz</Button
                >
                <Button
                    onclick={() => {
                        viewMode = "ideas";
                    }}
                    variant="outline"
                    selected={viewMode == "ideas"}><Lightbulb />Pomysły</Button
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
    </div>
    {#if viewMode == "dashboard"}
        <Dashboard />
    {:else if viewMode == "calendar"}
        <CalendarView />
    {:else if viewMode == "ideas"}
        <IdeasView />
    {/if}
</div>

{#if showAddTask}
    <AddTask
        onClose={() => {
            showAddTask = false;
        }}
    />
{/if}

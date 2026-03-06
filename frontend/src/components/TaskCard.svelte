<script lang="ts">
    import {
        CalendarClockIcon,
        Pencil,
        Trash2,
        Plus,
        ChevronRight,
        ChevronDown,
        CalendarCheckIcon,
        BatteryLow,
        BatteryMedium,
        Battery,
        BatteryWarning,
    } from "lucide-svelte";
    import type { Task } from "../lib/api";
    import { TaskStatus, EffortLevel } from "../lib/api";
    import { useTaskMutation } from "../lib/queries/tasks";

    interface Props {
        task: Task;
        send: any;
        receive: any;
        onEdit: (task: Task) => void;
        onAddChild: (parentId: number) => void;
        expanded?: boolean;
        onToggleExpand?: () => void;
    }

    let {
        task,
        send,
        receive,
        onEdit,
        onAddChild,
        expanded = false,
        onToggleExpand,
    }: Props = $props();

    const mutations = useTaskMutation();

    const isDone = $derived(task.status === TaskStatus.DONE);
    const hasChildren = $derived(task.children && task.children.length > 0);

    function toggleCompletion() {
        if (task.status === TaskStatus.TODO) {
            mutations.complete.mutate(task.id!);
        } else {
            mutations.uncomplete.mutate(task.id!);
        }
    }

    function handleDelete(e: MouseEvent) {
        e.stopPropagation();
        if (confirm(`Czy na pewno chcesz usunąć "${task.title}"?`)) {
            mutations.delete.mutate(task.id!);
        }
    }

    function handleEdit(e: MouseEvent) {
        e.stopPropagation();
        onEdit(task);
    }

    function handleAddChild(e: MouseEvent) {
        e.stopPropagation();
        onAddChild(task.id!);
    }

    const effortConfig: Record<
        EffortLevel,
        { icon: any; color: string; label: string }
    > = {
        [EffortLevel.S]: {
            icon: BatteryLow,
            color: "text-effort-s",
            label: "Quick win (< 15 min)",
        },
        [EffortLevel.M]: {
            icon: BatteryMedium,
            color: "text-effort-m",
            label: "Standard (~1 hour)",
        },
        [EffortLevel.L]: {
            icon: Battery,
            color: "text-effort-l",
            label: "Deep work (2–3 hours)",
        },
        [EffortLevel.XL]: {
            icon: BatteryWarning,
            color: "text-effort-xl",
            label: "Too big — needs breakdown!",
        },
    };

    const effortInfo = $derived(task.effort ? effortConfig[task.effort] : null);

    function handleToggleExpand(e: MouseEvent) {
        e.stopPropagation();
        if (onToggleExpand) {
            onToggleExpand();
        }
    }
</script>

<div
    class="p-4 border-2 border-muted-foreground/25 rounded-lg hover:shadow-md transition-shadow bg-card cursor-pointer relative group"
    class:opacity-60={isDone}
    in:receive={{ key: task.id }}
    out:send={{ key: task.id }}
    onclick={toggleCompletion}
    onkeydown={(e) => e.key === "Enter" && toggleCompletion()}
    role="button"
    tabindex="0"
>
    <!-- Expand/Collapse Button (if has children) -->
    {#if hasChildren}
        <button
            onclick={handleToggleExpand}
            class="absolute left-2 top-8 -translate-y-1/2 p-1 hover:bg-muted rounded transition-colors"
            aria-label={expanded ? "Collapse children" : "Expand children"}
            title={expanded ? "Collapse children" : "Expand children"}
        >
            {#if expanded}
                <ChevronDown size={20} />
            {:else}
                <ChevronRight size={20} />
            {/if}
        </button>
    {/if}

    <!-- Action Buttons (visible on hover) -->
    <div
        class="absolute top-2 right-2 flex gap-1
           opacity-100 lg:opacity-0 lg:group-hover:opacity-100
           transition-opacity"
    >
        <button
            onclick={handleAddChild}
            class="p-3 lg:p-2 bg-background hover:bg-primary hover:text-primary-foreground rounded-lg transition-colors"
            aria-label="Add subtask"
            title="Add subtask"
        >
            <Plus size={16} />
        </button>
        <button
            onclick={handleEdit}
            class="p-3 lg:p-2 bg-background hover:bg-muted rounded-lg transition-colors"
            aria-label="Edit task"
            title="Edit task"
        >
            <Pencil size={16} />
        </button>
        <button
            onclick={handleDelete}
            class="p-3 lg:p-2 bg-background hover:bg-destructive hover:text-destructive-foreground rounded-lg transition-colors"
            aria-label="Delete task"
            title="Delete task"
        >
            <Trash2 size={16} />
        </button>
    </div>

    <h3 class="text-md font-semibold pr-32" class:pl-8={hasChildren}>
        {task.title}
        {#if hasChildren}
            <span class="rounded-full bg-accent/50 pl-2 pr-2">
                {task.children?.length}
            </span>
        {/if}
    </h3>
    {#if task.description}
        <p class="text-foreground/80 mt-2">
            {task.description}
        </p>
    {/if}
    {#if task.scheduled_date}
        <span
            class="text-sm text-muted-foreground mt-2 flex gap-1 items-center"
        >
            <CalendarCheckIcon class="text-muted-foreground" />
            {new Date(task.scheduled_date).toLocaleDateString()}
        </span>
    {/if}
    {#if task.deadline}
        <span
            class="text-sm text-muted-foreground mt-2 flex gap-1 items-center"
        >
            <CalendarClockIcon class="text-muted-foreground" />
            {new Date(task.deadline).toLocaleDateString()}
        </span>
    {/if}
    {#if effortInfo}
        <span
            class="text-sm mt-2 flex gap-1 items-center {effortInfo.color}"
            title={effortInfo.label}
        >
            <effortInfo.icon size={16} />
            {task.effort}
        </span>
    {/if}
</div>

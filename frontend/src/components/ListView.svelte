<script lang="ts">
    import { crossfade } from "svelte/transition";
    import { quintOut } from "svelte/easing";
    import { flip } from "svelte/animate";
    import { slide } from "svelte/transition";
    import { useTasks } from "../lib/queries/tasks";
    import { TaskStatus, type Task } from "../lib/api";
    import TaskCard from "./TaskCard.svelte";
    import AddTask from "./AddTask.svelte";
    import Button from "./Button.svelte";
    import Dropdown from "./Dropdown.svelte";
    import { Zap } from "lucide-svelte";

    const [send, receive] = crossfade({
        duration: 400,
        easing: quintOut,
    });

    const tasksQuery = useTasks();

    const tasks = $derived(tasksQuery.data);
    const isLoading = $derived(tasksQuery.isLoading);
    const isError = $derived(tasksQuery.isError);

    let items_show_selected = $state("all");

    const items = [
        { label: "Dziś", value: "today" },
        { label: "Następnych 7 dni", value: "week" },
        { label: "Następnych 30 dni", value: "month" },
        { label: "Wszystkie", value: "all" },
    ];

    const tasksFromToday = $derived(() => {
        const now = new Date();
        return (
            tasks?.filter((task) => {
                if (task.scheduled_date) {
                    const scheduledDate = new Date(task.scheduled_date);
                    return scheduledDate.toDateString() === now.toDateString();
                }
                return false;
            }) ?? []
        );
    });

    const tasksFromNext7Days = $derived(() => {
        const now = new Date();
        const sevenDaysLater = new Date();
        sevenDaysLater.setDate(now.getDate() + 7);

        return (
            tasks?.filter((task) => {
                if (task.scheduled_date) {
                    const scheduledDate = new Date(task.scheduled_date);
                    return (
                        scheduledDate >= now && scheduledDate <= sevenDaysLater
                    );
                }
                return false;
            }) ?? []
        );
    });

    const tasksFromNext30Days = $derived(() => {
        const now = new Date();
        const thirtyDaysLater = new Date();
        thirtyDaysLater.setDate(now.getDate() + 30);

        return (
            tasks?.filter((task) => {
                if (task.scheduled_date) {
                    const scheduledDate = new Date(task.scheduled_date);
                    return (
                        scheduledDate >= now && scheduledDate <= thirtyDaysLater
                    );
                }
                return false;
            }) ?? []
        );
    });

    const doneTasks = $derived(
        items_show_selected === "today"
            ? tasksFromToday().filter((task) => task.status === TaskStatus.DONE)
            : items_show_selected === "week"
              ? tasksFromNext7Days().filter(
                    (task) => task.status === TaskStatus.DONE,
                )
              : items_show_selected === "month"
                ? tasksFromNext30Days().filter(
                      (task) => task.status === TaskStatus.DONE,
                  )
                : (tasks?.filter((task) => task.status === TaskStatus.DONE) ??
                  []),
    );

    const undoneTasks = $derived(
        items_show_selected === "today"
            ? tasksFromToday().filter((task) => task.status === TaskStatus.TODO)
            : items_show_selected === "week"
              ? tasksFromNext7Days().filter(
                    (task) => task.status === TaskStatus.TODO,
                )
              : items_show_selected === "month"
                ? tasksFromNext30Days().filter(
                      (task) => task.status === TaskStatus.TODO,
                  )
                : (tasks?.filter((task) => task.status === TaskStatus.TODO) ??
                  []),
    );

    let editingTask = $state<Task | undefined>(undefined);
    let addingChildToTaskId = $state<number | undefined>(undefined);

    // Expansion state for tasks with children
    let expandedTasks = $state<Set<number>>(new Set());

    function handleEdit(task: Task) {
        editingTask = task;
    }

    function handleAddChild(parentId: number) {
        addingChildToTaskId = parentId;
    }

    function closeModal() {
        editingTask = undefined;
        addingChildToTaskId = undefined;
    }

    function toggleExpand(taskId: number) {
        const newExpanded = new Set(expandedTasks);
        if (newExpanded.has(taskId)) {
            newExpanded.delete(taskId);
        } else {
            newExpanded.add(taskId);
        }
        expandedTasks = newExpanded;
    }

    function isExpanded(taskId: number): boolean {
        return expandedTasks.has(taskId);
    }

    // Recursive component to render task and its children
    function renderTaskWithChildren(
        task: Task,
        depth: number = 0,
    ): { task: Task; depth: number }[] {
        const result: { task: Task; depth: number }[] = [{ task, depth }];

        if (task.children && task.children.length > 0 && isExpanded(task.id!)) {
            for (const child of task.children) {
                result.push(...renderTaskWithChildren(child, depth + 1));
            }
        }

        return result;
    }

    // Flatten tasks with their depth for rendering
    const flatUndoneTasks = $derived(() => {
        const result: { task: Task; depth: number }[] = [];
        for (const task of undoneTasks) {
            result.push(...renderTaskWithChildren(task, 0));
        }
        return result;
    });

    const flatDoneTasks = $derived(() => {
        const result: { task: Task; depth: number }[] = [];
        for (const task of doneTasks) {
            result.push(...renderTaskWithChildren(task, 0));
        }
        return result;
    });
</script>

<div>
    {#if isLoading}
        <p>Ładowanie zadań...</p>
    {:else if isError}
        <p class="text-destructive">Błąd podczas ładowania zadań.</p>
    {:else if tasks && tasks.length === 0}
        <p>No tasks found. Enjoy your free time!</p>
    {:else if tasks}
        <!-- Undone Tasks -->
        <div class="mb-8">
            <div
                class="flex justify-start items-center content-start gap-4 mb-4"
            >
                <h2 class="text-xl font-bold">
                    Do zrobienia ({undoneTasks.length})
                </h2>
                <p>Pokaż zadania:</p>
                <Dropdown
                    class="flex"
                    value="all"
                    size="sm"
                    placeholder="Wybierz okres czasowy"
                    onchange={(new_value) => (items_show_selected = new_value)}
                    {items}
                />
            </div>
            {#if undoneTasks.length > 0}
                <ul class="space-y-2">
                    {#each flatUndoneTasks() as { task, depth } (task.id)}
                        <div
                            animate:flip={{ duration: 400 }}
                            transition:slide={{
                                duration: 300,
                                easing: quintOut,
                            }}
                            style="margin-left: {depth * 2}rem;"
                        >
                            <TaskCard
                                {task}
                                {send}
                                {receive}
                                onEdit={handleEdit}
                                onAddChild={handleAddChild}
                                expanded={isExpanded(task.id!)}
                                onToggleExpand={() => toggleExpand(task.id!)}
                            />
                        </div>
                    {/each}
                </ul>
            {:else}
                <p class="text-muted-foreground">Brak zadań do zrobienia!</p>
            {/if}
        </div>

        <!-- Done Tasks -->
        <div>
            <h2 class="text-xl font-bold mb-4">
                Zrobione ({doneTasks.length})
            </h2>
            {#if doneTasks.length > 0}
                <ul class="space-y-2">
                    {#each flatDoneTasks() as { task, depth } (task.id)}
                        <div
                            animate:flip={{ duration: 400 }}
                            transition:slide={{
                                duration: 300,
                                easing: quintOut,
                            }}
                            style="margin-left: {depth * 2}rem;"
                        >
                            <TaskCard
                                {task}
                                {send}
                                {receive}
                                onEdit={handleEdit}
                                onAddChild={handleAddChild}
                                expanded={isExpanded(task.id!)}
                                onToggleExpand={() => toggleExpand(task.id!)}
                            />
                        </div>
                    {/each}
                </ul>
            {:else}
                <p class="text-muted-foreground">Brak zrobionych zadań.</p>
            {/if}
        </div>
    {/if}
</div>

{#if editingTask}
    <AddTask task={editingTask} onClose={closeModal} />
{/if}

{#if addingChildToTaskId}
    <AddTask parentId={addingChildToTaskId} onClose={closeModal} />
{/if}

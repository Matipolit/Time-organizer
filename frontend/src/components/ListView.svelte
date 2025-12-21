<script lang="ts">
    import { crossfade } from "svelte/transition";
    import { quintOut } from "svelte/easing";
    import { flip } from "svelte/animate";
    import { slide } from "svelte/transition";
    import { useTasks } from "../lib/queries/tasks";
    import { TaskStatus, type Task } from "../lib/api";
    import TaskCard from "./TaskCard.svelte";
    import AddTask from "./AddTask.svelte";

    // Create crossfade transitions for smooth animations between lists
    const [send, receive] = crossfade({
        duration: 400,
        easing: quintOut,
    });

    const tasksQuery = useTasks();

    // Use $derived for Svelte 5 reactivity
    const tasks = $derived(tasksQuery.data);
    const isLoading = $derived(tasksQuery.isLoading);
    const isError = $derived(tasksQuery.isError);

    // Reactively split tasks into done and undone
    const doneTasks = $derived(
        tasks?.filter((task) => task.status === TaskStatus.DONE) ?? [],
    );
    const undoneTasks = $derived(
        tasks?.filter((task) => task.status === TaskStatus.TODO) ?? [],
    );

    // Edit task state
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
            <h2 class="text-xl font-bold mb-4">
                Do zrobienia ({undoneTasks.length})
            </h2>
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

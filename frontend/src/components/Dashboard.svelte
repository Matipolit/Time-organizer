<script lang="ts">
    import { crossfade } from "svelte/transition";
    import { quintOut } from "svelte/easing";
    import { flip } from "svelte/animate";
    import { slide } from "svelte/transition";
    import { useTasks } from "../lib/queries/tasks";
    import { TaskStatus, TaskType, type Task } from "../lib/api";
    import TaskCard from "./TaskCard.svelte";
    import AddTask from "./AddTask.svelte";
    import Button from "./Button.svelte";
    import Dropdown from "./Dropdown.svelte";
    import {
        CalendarClockIcon,
        IterationCwIcon,
        SquareCheckBigIcon,
        ListTodo,
        Zap,
        ChevronRight,
        ChevronDown,
    } from "lucide-svelte";

    import { getCookie, setCookie } from "../lib/cookies";
    import { untrack } from "svelte";

    const [send, receive] = crossfade({
        duration: 400,
        easing: quintOut,
    });

    const tasksQuery = useTasks();

    const tasks = $derived(tasksQuery.data);
    const isLoading = $derived(tasksQuery.isLoading);
    const isError = $derived(tasksQuery.isError);

    const items = [
        { label: "Dziś", value: "today" },
        { label: "Następnych 7 dni", value: "week" },
        { label: "Następnych 30 dni", value: "month" },
        { label: "Wszystkie", value: "all" },
    ];

    let items_show_selected = $state(getCookie("items_show_selected") ?? "all");

    let isMounted = false;

    let showDoneDeadline = $state(false);
    let showDoneTodo = $state(false);
    let showDoneChore = $state(false);
    let showDoneStreak = $state(false);

    function processDoneTasks(list: { task: Task; depth: number }[]) {
        return list.sort((a, b) => {
            const dateA = a.task.last_completed_at
                ? new Date(a.task.last_completed_at).getTime()
                : 0;
            const dateB = b.task.last_completed_at
                ? new Date(b.task.last_completed_at).getTime()
                : 0;
            return dateB - dateA;
        });
    }

    $effect(() => {
        // We access state to register the dependency
        const currentSelection = items_show_selected;

        if (!isMounted) {
            isMounted = true;
            return;
        }

        // This code only runs on subsequent updates
        untrack(() => {
            console.log("Saving preference to cookie.");
            setCookie("items_show_selected", currentSelection, 30);
        });
    });

    function isInTimeWindow(task: Task, window: string): boolean {
        if (!task.scheduled_date) return window === "all";
        const scheduledDate = new Date(task.scheduled_date);
        const now = new Date();
        if (window === "today") {
            return scheduledDate.toDateString() === now.toDateString();
        }
        if (window === "week") {
            const limit = new Date();
            limit.setDate(now.getDate() + 7);
            return scheduledDate >= now && scheduledDate <= limit;
        }
        if (window === "month") {
            const limit = new Date();
            limit.setDate(now.getDate() + 30);
            return scheduledDate >= now && scheduledDate <= limit;
        }
        return true; // "all"
    }

    function flattenTasks(list: Task[]): { task: Task; depth: number }[] {
        const result: { task: Task; depth: number }[] = [];
        for (const task of list) {
            result.push(...renderTaskWithChildren(task, 0));
        }
        return result;
    }

    function splitFlatTasks(list: Task[]) {
        return {
            undone: flattenTasks(
                list.filter(
                    (t) =>
                        t.status !== TaskStatus.DONE &&
                        t.status !== TaskStatus.IN_PROGRESS,
                ),
            ),
            done: flattenTasks(
                list.filter((t) => t.status === TaskStatus.DONE),
            ),
        };
    }

    function filterUndoneTasks(list: Task[]) {
        return list.filter(
            (t) =>
                t.status !== TaskStatus.DONE &&
                t.status !== TaskStatus.IN_PROGRESS,
        );
    }

    function filterDoneTasks(list: Task[]) {
        return list.filter((t) => t.status === TaskStatus.DONE);
    }

    const todoTasks = $derived(
        tasks?.filter((task) => task.task_type === TaskType.TODO) ?? [],
    );

    const deadlineTasks = $derived(
        tasks?.filter((task) => task.task_type === TaskType.DEADLINE) ?? [],
    );

    const choreTasks = $derived(
        tasks?.filter((task) => task.task_type === TaskType.CHORE) ?? [],
    );

    const streakTasks = $derived(
        tasks?.filter((task) => task.task_type === TaskType.STREAK) ?? [],
    );

    const visibleTodoTasks = $derived(
        todoTasks.filter((task) => isInTimeWindow(task, items_show_selected)),
    );

    const flatTodoTasks = $derived(splitFlatTasks(visibleTodoTasks));

    const visibleDeadlineTasks = $derived(
        deadlineTasks.filter((task) =>
            isInTimeWindow(task, items_show_selected),
        ),
    );

    const flatDeadlineTasks = $derived(splitFlatTasks(visibleDeadlineTasks));

    const visibleChoreTasks = $derived(
        (
            tasks?.filter((task) => task.task_type === TaskType.CHORE) ?? []
        ).filter((task) => isInTimeWindow(task, items_show_selected)),
    );
    const flatChoreTasks = $derived(splitFlatTasks(visibleChoreTasks));

    const visibleStreakTasks = $derived(
        (
            tasks?.filter((task) => task.task_type === TaskType.STREAK) ?? []
        ).filter((task) => isInTimeWindow(task, items_show_selected)),
    );
    const flatStreakTasks = $derived(splitFlatTasks(visibleStreakTasks));

    type TabType = "todo" | "deadline" | "chore" | "streak";
    let activeTab = $state<TabType>("todo");

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

    const inProgressTask = $derived(
        tasks?.find((task) => task.status === TaskStatus.IN_PROGRESS),
    );

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
</script>

<div class="h-full flex flex-col overflow-hidden">
    {#if inProgressTask}
        <div
            class="mb-8 p-6 border-4 border-primary rounded-xl bg-primary/5 shadow-lg shrink-0"
        >
            <h2
                class="text-2xl font-bold text-primary mb-4 flex items-center gap-2"
            >
                <Zap class="text-primary fill-primary" />
                W trakcie
            </h2>
            <TaskCard
                task={inProgressTask}
                {send}
                {receive}
                onEdit={handleEdit}
                onAddChild={handleAddChild}
                expanded={isExpanded(inProgressTask.id!)}
                onToggleExpand={() => toggleExpand(inProgressTask.id!)}
            />
        </div>
    {/if}

    <!-- Mobile tab bar -->
    <div class="flex lg:hidden border-b border-muted mb-4 shrink-0">
        <button
            class="flex-1 flex gap-2 items-center justify-center py-2 text-sm font-medium border-b-2 transition-colors {activeTab ===
            'todo'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground'}"
            onclick={() => (activeTab = "todo")}
        >
            <ListTodo size={16} />
            Zadania
            <span class="rounded-full bg-accent px-1.5 text-xs"
                >{filterUndoneTasks(todoTasks).length}</span
            >
        </button>
        <button
            class="flex-1 flex gap-2 items-center justify-center py-2 text-sm font-medium border-b-2 transition-colors {activeTab ===
            'deadline'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground'}"
            onclick={() => (activeTab = "deadline")}
        >
            <CalendarClockIcon size={16} />
            Deadline
            <span class="rounded-full bg-accent px-1.5 text-xs"
                >{filterUndoneTasks(deadlineTasks).length}</span
            >
        </button>
        <button
            class="flex-1 flex gap-2 items-center justify-center py-2 text-sm font-medium border-b-2 transition-colors {activeTab ===
            'chore'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground'}"
            onclick={() => (activeTab = "chore")}
        >
            <IterationCwIcon size={16} />
            Obowiązki
            <span class="rounded-full bg-accent px-1.5 text-xs"
                >{filterUndoneTasks(choreTasks).length}</span
            >
        </button>
        <button
            class="flex-1 flex gap-2 items-center justify-center py-2 text-sm font-medium border-b-2 transition-colors {activeTab ===
            'streak'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground'}"
            onclick={() => (activeTab = "streak")}
        >
            <SquareCheckBigIcon size={16} />
            Streaki
        </button>
    </div>

    <div class="flex-1 min-h-0 flex lg:divide-x lg:divide-muted">
        {#if isLoading}
            <p>Ładowanie zadań...</p>
        {:else if isError}
            <p class="text-destructive">Błąd podczas ładowania zadań.</p>
        {/if}

        <!-- Todo task list -->
        <div
            class="w-full lg:w-1/4 shrink-0 lg:pr-4 h-full overflow-y-auto {activeTab !==
            'todo'
                ? 'hidden lg:block'
                : ''}"
        >
            <div
                class="hidden lg:flex justify-between items-center content-start gap-4 mb-4 sticky top-0 bg-background z-10 py-2"
            >
                <h2 class="text-xl font-bold flex gap-3 items-center">
                    <span class="rounded-full bg-accent pl-2 pr-2">
                        {filterUndoneTasks(todoTasks).length}
                    </span>
                    <span class="flex gap-1 items-center justify-center">
                        <ListTodo />
                        Zadania
                    </span>
                </h2>
                <Dropdown
                    class="flex"
                    bind:value={items_show_selected}
                    size="sm"
                    placeholder="Wybierz okres czasowy"
                    onchange={(new_value) => (items_show_selected = new_value)}
                    {items}
                />
            </div>
            {#if filterUndoneTasks(todoTasks).length > 0}
                <ul class="space-y-2 pb-4">
                    {#each flatTodoTasks.undone as { task, depth } (task.id)}
                        <div
                            animate:flip={{ duration: 100 }}
                            transition:slide={{
                                duration: 100,
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
                <p class="text-muted-foreground">Brak zadań</p>
            {/if}

            {#if flatTodoTasks.done.length > 0}
                <div class="mt-8 border-t border-muted pt-4">
                    <button
                        onclick={() => (showDoneTodo = !showDoneTodo)}
                        class="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium mb-4"
                    >
                        {#if showDoneTodo}
                            <ChevronDown size={16} />
                        {:else}
                            <ChevronRight size={16} />
                        {/if}
                        Zakończone ({flatTodoTasks.done.length})
                    </button>
                    {#if showDoneTodo}
                        <ul class="space-y-2 pb-4">
                            {#each processDoneTasks(flatTodoTasks.done).slice(0, 50) as { task, depth } (task.id)}
                                <div style="margin-left: {depth * 2}rem;">
                                    <TaskCard
                                        {task}
                                        {send}
                                        {receive}
                                        onEdit={handleEdit}
                                        onAddChild={handleAddChild}
                                        expanded={isExpanded(task.id!)}
                                        onToggleExpand={() =>
                                            toggleExpand(task.id!)}
                                    />
                                </div>
                            {/each}
                            {#if flatTodoTasks.done.length > 50}
                                <p
                                    class="text-xs text-center text-muted-foreground italic mt-4"
                                >
                                    Pokazano 50 z {flatTodoTasks.done.length}
                                    zadań.
                                </p>
                            {/if}
                        </ul>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- Deadline task list -->
        <div
            class="w-full lg:w-1/4 shrink-0 lg:px-4 h-full overflow-y-auto {activeTab !==
            'deadline'
                ? 'hidden lg:block'
                : ''}"
        >
            <div
                class="hidden lg:flex justify-between items-center content-start gap-4 mb-4 sticky top-0 bg-background z-10 py-2"
            >
                <h2 class="text-xl font-bold flex gap-3 items-center">
                    <span class="rounded-full bg-accent pl-2 pr-2">
                        {filterUndoneTasks(deadlineTasks).length}
                    </span>
                    <span class="flex gap-1 items-center justify-center">
                        <CalendarClockIcon />
                        Deadline
                    </span>
                </h2>
            </div>
            {#if filterUndoneTasks(deadlineTasks).length > 0}
                <ul class="space-y-2 pb-4">
                    {#each flatDeadlineTasks.undone as { task, depth } (task.id)}
                        <div
                            animate:flip={{ duration: 100 }}
                            transition:slide={{
                                duration: 100,
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
                <p class="text-muted-foreground">Brak zadań z deadlinem</p>
            {/if}

            {#if flatDeadlineTasks.done.length > 0}
                <div class="mt-8 border-t border-muted pt-4">
                    <button
                        onclick={() => (showDoneDeadline = !showDoneDeadline)}
                        class="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium mb-4"
                    >
                        {#if showDoneDeadline}
                            <ChevronDown size={16} />
                        {:else}
                            <ChevronRight size={16} />
                        {/if}
                        Zakończone ({flatDeadlineTasks.done.length})
                    </button>
                    {#if showDoneDeadline}
                        <ul class="space-y-2 pb-4">
                            {#each processDoneTasks(flatDeadlineTasks.done).slice(0, 50) as { task, depth } (task.id)}
                                <div style="margin-left: {depth * 2}rem;">
                                    <TaskCard
                                        {task}
                                        {send}
                                        {receive}
                                        onEdit={handleEdit}
                                        onAddChild={handleAddChild}
                                        expanded={isExpanded(task.id!)}
                                        onToggleExpand={() =>
                                            toggleExpand(task.id!)}
                                    />
                                </div>
                            {/each}
                            {#if flatDeadlineTasks.done.length > 50}
                                <p
                                    class="text-xs text-center text-muted-foreground italic mt-4"
                                >
                                    Pokazano 50 z {flatDeadlineTasks.done
                                        .length}
                                    zadań.
                                </p>
                            {/if}
                        </ul>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- chores -->
        <div
            class="w-full lg:w-1/4 shrink-0 lg:px-4 h-full overflow-y-auto {activeTab !==
            'chore'
                ? 'hidden lg:block'
                : ''}"
        >
            <div
                class="hidden lg:flex justify-between items-center content-start gap-4 mb-4 sticky top-0 bg-background z-10 py-2"
            >
                <h2 class="flex text-xl font-bold gap-3 items-center">
                    <span class="rounded-full bg-accent pl-2 pr-2">
                        {filterUndoneTasks(choreTasks).length}
                    </span>
                    <span class="flex gap-1 items-center justify-center">
                        <IterationCwIcon />
                        Obowiązki
                    </span>
                </h2>
            </div>

            {#if filterUndoneTasks(choreTasks).length > 0}
                <ul class="space-y-2 pb-4">
                    {#each flatChoreTasks.undone as { task, depth } (task.id)}
                        <div
                            animate:flip={{ duration: 100 }}
                            transition:slide={{
                                duration: 100,
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
                <p class="text-muted-foreground">Brak obowiązków na dziś</p>
            {/if}

            {#if flatChoreTasks.done.length > 0}
                <div class="mt-8 border-t border-muted pt-4">
                    <button
                        onclick={() => (showDoneChore = !showDoneChore)}
                        class="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium mb-4"
                    >
                        {#if showDoneChore}
                            <ChevronDown size={16} />
                        {:else}
                            <ChevronRight size={16} />
                        {/if}
                        Zakończone ({flatChoreTasks.done.length})
                    </button>
                    {#if showDoneChore}
                        <ul class="space-y-2 pb-4">
                            {#each processDoneTasks(flatChoreTasks.done).slice(0, 50) as { task, depth } (task.id)}
                                <div style="margin-left: {depth * 2}rem;">
                                    <TaskCard
                                        {task}
                                        {send}
                                        {receive}
                                        onEdit={handleEdit}
                                        onAddChild={handleAddChild}
                                        expanded={isExpanded(task.id!)}
                                        onToggleExpand={() =>
                                            toggleExpand(task.id!)}
                                    />
                                </div>
                            {/each}
                            {#if flatChoreTasks.done.length > 50}
                                <p
                                    class="text-xs text-center text-muted-foreground italic mt-4"
                                >
                                    Pokazano 50 z {flatChoreTasks.done.length}
                                    zadań.
                                </p>
                            {/if}
                        </ul>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- streaks -->

        <div
            class="w-full lg:w-1/4 shrink-0 lg:pl-4 h-full overflow-y-auto {activeTab !==
            'streak'
                ? 'hidden lg:block'
                : ''}"
        >
            <div
                class="hidden lg:flex justify-between items-center content-start gap-4 mb-4 sticky top-0 bg-background z-10 py-2"
            >
                <h2 class="text-xl font-bold flex gap-3 items-center">
                    <span class="rounded-full bg-accent pl-2 pr-2">
                        {filterUndoneTasks(streakTasks).length}
                    </span>
                    <span class="flex gap-1 items-center justify-center">
                        <SquareCheckBigIcon />
                        Streaki
                    </span>
                </h2>
            </div>
            {#if filterUndoneTasks(streakTasks).length > 0}
                <ul class="space-y-2 pb-4">
                    {#each flatStreakTasks.undone as { task, depth } (task.id)}
                        <div
                            animate:flip={{ duration: 100 }}
                            transition:slide={{
                                duration: 100,
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
            {/if}

            {#if flatStreakTasks.done.length > 0}
                <div class="mt-8 border-t border-muted pt-4">
                    <button
                        onclick={() => (showDoneStreak = !showDoneStreak)}
                        class="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium mb-4"
                    >
                        {#if showDoneStreak}
                            <ChevronDown size={16} />
                        {:else}
                            <ChevronRight size={16} />
                        {/if}
                        Zakończone ({flatStreakTasks.done.length})
                    </button>
                    {#if showDoneStreak}
                        <ul class="space-y-2 pb-4">
                            {#each processDoneTasks(flatStreakTasks.done).slice(0, 50) as { task, depth } (task.id)}
                                <div style="margin-left: {depth * 2}rem;">
                                    <TaskCard
                                        {task}
                                        {send}
                                        {receive}
                                        onEdit={handleEdit}
                                        onAddChild={handleAddChild}
                                        expanded={isExpanded(task.id!)}
                                        onToggleExpand={() =>
                                            toggleExpand(task.id!)}
                                    />
                                </div>
                            {/each}
                            {#if flatStreakTasks.done.length > 50}
                                <p
                                    class="text-xs text-center text-muted-foreground italic mt-4"
                                >
                                    Pokazano 50 z {flatStreakTasks.done.length}
                                    zadań.
                                </p>
                            {/if}
                        </ul>
                    {/if}
                </div>
            {/if}
        </div>
    </div>
</div>

{#if editingTask}
    <AddTask task={editingTask} onClose={closeModal} />
{/if}

{#if addingChildToTaskId}
    <AddTask parentId={addingChildToTaskId} onClose={closeModal} />
{/if}

<script lang="ts">
    import { X } from "lucide-svelte";
    import { useTaskMutation } from "../lib/queries/tasks";
    import { TaskType, TaskStatus, EffortLevel, type Task } from "../lib/api";
    import Button from "./Button.svelte";

    interface Props {
        task?: Task;
        parentId?: number;
        onClose: () => void;
    }

    let { task, parentId, onClose }: Props = $props();

    const mutations = useTaskMutation();

    // Initialize form state
    let title = $state(task?.title ?? "");
    let description = $state(task?.description ?? "");
    let taskType = $state(task?.task_type ?? TaskType.DEADLINE);
    let scheduledDate = $state(task?.scheduled_date?.split("T")[0] ?? "");
    let effort = $state(task?.effort ?? EffortLevel.M);
    let deadline = $state(task?.deadline?.split("T")[0] ?? "");
    let recurrenceIntervalDays = $state(
        task?.recurrence_interval_days?.toString() ?? "7",
    );

    const isEditMode = !!task;

    function handleSubmit() {
        const taskData: Partial<Task> = {
            title,
            description: description || undefined,
            task_type: taskType,
            status: task?.status ?? TaskStatus.TODO,
            scheduled_date: scheduledDate || undefined,
            effort: effort || undefined,
            parent_id: parentId || task?.parent_id,
        };

        // Add type-specific fields
        if (taskType === TaskType.DEADLINE && deadline) {
            taskData.deadline = deadline;
        }

        if (taskType === TaskType.CHORE && recurrenceIntervalDays) {
            taskData.recurrence_interval_days = parseInt(
                recurrenceIntervalDays,
                10,
            );
        }

        if (isEditMode && task?.id) {
            mutations.update.mutate(
                { id: task.id, updates: taskData },
                {
                    onSuccess: () => {
                        onClose();
                    },
                },
            );
        } else {
            mutations.create.mutate(taskData, {
                onSuccess: () => {
                    onClose();
                },
            });
        }
    }
</script>

<div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    onclick={onClose}
    onkeydown={(e) => e.key === "Escape" && onClose()}
    role="button"
    tabindex="-1"
>
    <div
        class="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onclick={(e) => e.stopPropagation()}
        onkeydown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        tabindex="0"
    >
        <div
            class="sticky top-0 bg-card border-b p-4 flex justify-between items-center"
        >
            <h2 class="text-2xl font-bold">
                {isEditMode
                    ? "Edytuj zadanie"
                    : parentId
                      ? "Dodaj podzadanie"
                      : "Dodaj nowe zadanie"}
            </h2>
            <button
                onclick={onClose}
                class="p-2 hover:bg-muted rounded-lg transition-colors"
                aria-label="Zamknij"
            >
                <X />
            </button>
        </div>

        <form
            onsubmit={(e) => {
                e.preventDefault();
                handleSubmit();
            }}
            class="p-6 space-y-6"
        >
            <!-- Title -->
            <div>
                <label for="title" class="block font-semibold mb-2">
                    Tytuł <span class="text-destructive">*</span>
                </label>
                <input
                    id="title"
                    type="text"
                    bind:value={title}
                    required
                    class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Co musi zostać zrobione?"
                />
            </div>

            <!-- Description -->
            <div>
                <label for="description" class="block font-semibold mb-2">
                    Opis
                </label>
                <textarea
                    id="description"
                    bind:value={description}
                    rows="3"
                    class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                    placeholder="Dodaj szczegóły ..."
                ></textarea>
            </div>

            <!-- Task Type -->
            <div>
                <label for="taskType" class="block font-semibold mb-2">
                    Typ zadania <span class="text-destructive">*</span>
                </label>
                <select
                    id="taskType"
                    bind:value={taskType}
                    class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    <option value={TaskType.DEADLINE}>Deadline</option>
                    <option value={TaskType.CHORE}>Powtarzalny obowiązek</option
                    >
                    <option value={TaskType.STREAK}>Streak</option>
                </select>
            </div>

            <div>
                <label for="effort" class="block font-semibold mb-2">
                    Poziom wysiłku
                </label>
                <select
                    id="effort"
                    bind:value={effort}
                    class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    <option value={EffortLevel.S}>S - Mały({"<"} 15 min)</option
                    >
                    <option value={EffortLevel.M}>M - Średni (~1 godz.)</option>
                    <option value={EffortLevel.L}>L - Duży (~2-3 godz.)</option>
                    <option value={EffortLevel.XL}
                        >XL - Zbyt duży (do podziału)</option
                    >
                </select>
            </div>
            <div>
                <label for="scheduledDate" class="block font-semibold mb-2">
                    Miękki deadline
                </label>
                <input
                    id="scheduledDate"
                    type="date"
                    bind:value={scheduledDate}
                    class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
            </div>

            {#if taskType === TaskType.DEADLINE}
                <div>
                    <label for="deadline" class="block font-semibold mb-2">
                        Deadline
                    </label>
                    <input
                        id="deadline"
                        type="date"
                        bind:value={deadline}
                        class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            {/if}

            <!-- Chore-specific fields -->
            {#if taskType === TaskType.CHORE}
                <div>
                    <label
                        for="recurrenceIntervalDays"
                        class="block font-semibold mb-2"
                    >
                        Recurrence Interval (days)
                    </label>
                    <input
                        id="recurrenceIntervalDays"
                        type="number"
                        bind:value={recurrenceIntervalDays}
                        min="1"
                        class="w-full p-3 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            {/if}

            <!-- Action Buttons -->
            <div class="flex gap-3 pt-4">
                <Button
                    type="submit"
                    variant="primary"
                    disabled={!title.trim() ||
                        mutations.create.isPending ||
                        mutations.update.isPending}
                    class="flex-1"
                >
                    {#if mutations.create.isPending || mutations.update.isPending}
                        Zapisywanie...
                    {:else}
                        {isEditMode ? "Zapisz zmiany" : "Dodaj zadanie"}
                    {/if}
                </Button>
                <Button
                    type="button"
                    variant="outline"
                    onclick={onClose}
                    class="flex-1"
                >
                    Anuluj
                </Button>
            </div>

            {#if mutations.create.isError || mutations.update.isError}
                <p class="text-destructive text-sm">
                    Error: {mutations.create.error?.message ||
                        mutations.update.error?.message}
                </p>
            {/if}
        </form>
    </div>
</div>

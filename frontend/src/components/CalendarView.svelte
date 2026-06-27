<script lang="ts">
    import { ChevronLeft, ChevronRight, IterationCwIcon } from "lucide-svelte";
    import { TaskStatus, type Task } from "../lib/api";
    import { useTasks } from "../lib/queries/tasks";

    const months = [
        "Styczeń",
        "Luty",
        "Marzec",
        "Kwiecień",
        "Maj",
        "Czerwiec",
        "Lipiec",
        "Sierpień",
        "Wrzesień",
        "Październik",
        "Listopad",
        "Grudzień",
    ];
    const weekDays = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"];

    type CalendarDay = {
        date: Date;
        dayOfMonth: number;
        isCurrentMonth: boolean;
        isToday: boolean;
        tasks: Task[];
    };

    const tasksQuery = useTasks();

    const tasks = $derived(tasksQuery.data ?? []);
    const isLoading = $derived(tasksQuery.isLoading);
    const isError = $derived(tasksQuery.isError);
    const currentDate = new Date();

    let diffFromNow = $state(0);

    const targetDate = $derived.by(() => {
        return new Date(
            currentDate.getFullYear(),
            currentDate.getMonth() + diffFromNow,
            1,
        );
    });

    const selectedMonth = $derived(targetDate.getMonth());
    const selectedYear = $derived(targetDate.getFullYear());

    const firstDayOfSelectedMonth = $derived(
        new Date(selectedYear, selectedMonth, 1),
    );
    const lastDayOfSelectedMonth = $derived(
        new Date(selectedYear, selectedMonth + 1, 0),
    );

    function dateKey(date: Date) {
        return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
    }

    function taskDueDate(task: Task) {
        const dueDate = task.scheduled_date ?? task.deadline;
        return dueDate ? new Date(dueDate) : null;
    }

    function flattenTasks(tasksToFlatten: Task[]) {
        const flatTasks: Task[] = [];
        const stack = [...tasksToFlatten].reverse();

        while (stack.length > 0) {
            const task = stack.pop();
            if (!task) continue;

            flatTasks.push(task);

            if (task.children?.length) {
                stack.push(...[...task.children].reverse());
            }
        }

        return flatTasks;
    }

    const flatTasks = $derived(flattenTasks(tasks));

    const tasksByDay = $derived.by(() => {
        const grouped = new Map<string, Task[]>();

        for (const task of flatTasks) {
            const dueDate = taskDueDate(task);
            if (!dueDate || Number.isNaN(dueDate.getTime())) continue;

            const key = dateKey(dueDate);
            const dayTasks = grouped.get(key);
            if (dayTasks) {
                dayTasks.push(task);
            } else {
                grouped.set(key, [task]);
            }
        }

        return grouped;
    });

    const calendarDays = $derived.by<CalendarDay[]>(() => {
        const days: CalendarDay[] = [];
        const firstWeekDay = (firstDayOfSelectedMonth.getDay() + 6) % 7;
        const daysInSelectedMonth = lastDayOfSelectedMonth.getDate();
        const totalDays =
            Math.ceil((firstWeekDay + daysInSelectedMonth) / 7) * 7;

        for (let index = 0; index < totalDays; index++) {
            const date = new Date(
                selectedYear,
                selectedMonth,
                index - firstWeekDay + 1,
            );

            days.push({
                date,
                dayOfMonth: date.getDate(),
                isCurrentMonth: date.getMonth() === selectedMonth,
                isToday: dateKey(date) === dateKey(currentDate),
                tasks: tasksByDay.get(dateKey(date)) ?? [],
            });
        }

        return days;
    });

    function increaseMonth() {
        diffFromNow += 1;
    }

    function decreaseMonth() {
        diffFromNow -= 1;
    }

    function resetToCurrent() {
        diffFromNow = 0;
    }
</script>

<div class="flex items-center gap-4" id="header">
    <button
        class="rounded-md p-1 hover:bg-accent"
        onclick={decreaseMonth}
        title="Previous month"
        aria-label="Previous month"
    >
        <ChevronLeft />
    </button>
    <button
        class="rounded-md p-1 hover:bg-accent"
        onclick={increaseMonth}
        title="Next month"
        aria-label="Next month"
    >
        <ChevronRight />
    </button>
    {#if diffFromNow != 0}
        <button
            class="rounded-md p-1 hover:bg-accent"
            onclick={resetToCurrent}
            title="Reset to current month"
            aria-label="Reset to current month"
        >
            <IterationCwIcon size={16} />
        </button>
    {/if}
    <h3 class="text-xl">
        <b>{months[selectedMonth]}</b>
        {selectedYear}
    </h3>
</div>
{#if isLoading}
    <p class="py-4 text-sm text-muted-foreground">Ładowanie zadań…</p>
{:else if isError}
    <p class="py-4 text-sm text-destructive">Nie udało się załadować zadań.</p>
{:else}
    <div
        id="calendarGrid"
        class="mt-4 overflow-hidden rounded-lg border border-muted"
    >
        <div class="grid grid-cols-7 border-b border-muted bg-muted/40">
            {#each weekDays as weekDay}
                <div
                    class="px-2 py-2 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                >
                    {weekDay}
                </div>
            {/each}
        </div>

        <div class="grid grid-cols-7 bg-muted/30">
            {#each calendarDays as day (dateKey(day.date))}
                <div
                    class="min-h-28 border-b border-r border-muted p-2 {day.isToday
                        ? 'bg-primary/10'
                        : day.isCurrentMonth
                          ? 'bg-card'
                          : 'bg-muted/30 text-muted-foreground'}"
                >
                    <div class="mb-2 flex items-center justify-between">
                        <span
                            class="flex h-6 w-6 items-center justify-center rounded-full text-sm {day.isToday
                                ? 'bg-primary font-semibold text-primary-foreground'
                                : ''}"
                        >
                            {day.dayOfMonth}
                        </span>
                    </div>

                    {#if day.tasks.length > 0}
                        <ul class="space-y-1">
                            {#each day.tasks as task, taskIndex (`${task.id ?? task.title}-${taskIndex}`)}
                                <li
                                    class="truncate rounded bg-primary px-2 py-1 text-xs text-primary-foreground {task.status ===
                                    TaskStatus.DONE
                                        ? 'opacity-50'
                                        : ''}"
                                    title={task.title}
                                >
                                    {task.title}
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </div>
            {/each}
        </div>
    </div>
{/if}

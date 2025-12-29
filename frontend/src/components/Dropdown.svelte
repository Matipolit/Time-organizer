<script lang="ts">
    import type { Snippet } from "svelte";
    import { fade, scale } from "svelte/transition";
    import { cubicOut } from "svelte/easing";

    interface DropdownItem {
        label: string;
        value: string;
        disabled?: boolean;
        icon?: Snippet;
    }

    interface Props {
        items: DropdownItem[];
        value?: string;
        placeholder?: string;
        disabled?: boolean;
        size?: "sm" | "md" | "lg";
        variant?: "default" | "outline" | "ghost";
        class?: string;
        onchange?: (value: string) => void;
        label?: string;
        error?: string;
    }

    let {
        items = [],
        value = $bindable(),
        placeholder = "Select an option",
        disabled = false,
        size = "md",
        variant = "default",
        class: className = "",
        onchange,
        label,
        error,
    }: Props = $props();

    let isOpen = $state(false);
    let dropdownRef: HTMLDivElement;

    const selectedItem = $derived(items.find((item) => item.value === value));

    const sizeClasses = {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
    };

    const variantClasses = {
        default: "bg-background border border-input hover:border-ring",
        outline:
            "bg-transparent border border-border hover:border-foreground/30",
        ghost: "bg-transparent hover:bg-muted",
    };

    const dropdownClasses = $derived(`
        relative inline-flex items-center justify-between gap-2
        rounded-[var(--radius)] transition-all cursor-pointer
        whitespace-nowrap w-full font-medium
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${error ? "border-destructive" : ""}
        ${className}
    `);

    function toggleDropdown() {
        if (!disabled) {
            isOpen = !isOpen;
        }
    }

    function selectItem(item: DropdownItem) {
        if (!item.disabled) {
            value = item.value;
            isOpen = false;
            onchange?.(item.value);
        }
    }

    function handleClickOutside(event: MouseEvent) {
        if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
            isOpen = false;
        }
    }

    function handleKeydown(event: KeyboardEvent) {
        if (disabled) return;

        switch (event.key) {
            case "Enter":
            case " ":
                event.preventDefault();
                toggleDropdown();
                break;
            case "Escape":
                isOpen = false;
                break;
            case "ArrowDown":
                event.preventDefault();
                if (!isOpen) {
                    isOpen = true;
                } else {
                    // Focus next item logic can be added here
                }
                break;
            case "ArrowUp":
                event.preventDefault();
                if (isOpen) {
                    // Focus previous item logic can be added here
                }
                break;
        }
    }

    function handleItemKeydown(event: KeyboardEvent, item: DropdownItem) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectItem(item);
        }
    }

    $effect(() => {
        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
            return () => {
                document.removeEventListener("mousedown", handleClickOutside);
            };
        }
    });
</script>

<div class="dropdown-container w-fit">
    {#if label}
        <label
            for="dropdown-button"
            class="block text-sm font-medium text-foreground mb-1.5"
        >
            {label}
        </label>
    {/if}

    <div class="relative" bind:this={dropdownRef}>
        <button
            id="dropdown-button"
            type="button"
            class={dropdownClasses}
            onclick={toggleDropdown}
            onkeydown={handleKeydown}
            {disabled}
            aria-haspopup="listbox"
            aria-expanded={isOpen}
        >
            <span class="flex items-center gap-2 flex-1 text-left">
                {#if selectedItem?.icon}
                    {@render selectedItem.icon()}
                {/if}
                <span
                    class={selectedItem
                        ? "text-foreground"
                        : "text-muted-foreground"}
                >
                    {selectedItem?.label || placeholder}
                </span>
            </span>
            <svg
                class="w-4 h-4 transition-transform text-muted-foreground"
                class:rotate-180={isOpen}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                />
            </svg>
        </button>

        {#if isOpen}
            <div
                class="absolute z-50 w-full mt-2 bg-popover border border-border rounded-(--radius) shadow-lg overflow-hidden"
                transition:scale={{
                    duration: 150,
                    easing: cubicOut,
                    start: 0.95,
                    opacity: 0,
                }}
                role="listbox"
            >
                <div class="max-h-60 overflow-y-auto py-1">
                    {#each items as item (item.value)}
                        <button
                            type="button"
                            class="w-full px-4 py-2 text-left text-sm transition-colors
                                   hover:bg-accent hover:text-accent-foreground
                                   disabled:opacity-50 disabled:cursor-not-allowed
                                   flex items-center gap-2
                                   {item.value === value
                                ? 'bg-accent/50 text-accent-foreground'
                                : 'text-popover-foreground'}"
                            onclick={() => selectItem(item)}
                            onkeydown={(e) => handleItemKeydown(e, item)}
                            disabled={item.disabled}
                            role="option"
                            aria-selected={item.value === value}
                        >
                            {#if item.icon}
                                {@render item.icon()}
                            {/if}
                            <span class="flex-1">{item.label}</span>
                            {#if item.value === value}
                                <svg
                                    class="w-4 h-4"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M5 13l4 4L19 7"
                                    />
                                </svg>
                            {/if}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}
    </div>

    {#if error}
        <p
            class="mt-1.5 text-sm text-destructive"
            transition:fade={{ duration: 150 }}
        >
            {error}
        </p>
    {/if}
</div>

<style>
    .dropdown-container {
        position: relative;
    }

    button:focus-visible {
        outline: 2px solid hsl(var(--ring));
        outline-offset: 2px;
    }

    /* Smooth scrollbar styling */
    .max-h-60::-webkit-scrollbar {
        width: 8px;
    }

    .max-h-60::-webkit-scrollbar-track {
        background: hsl(var(--muted));
        border-radius: var(--radius);
    }

    .max-h-60::-webkit-scrollbar-thumb {
        background: hsl(var(--muted-foreground) / 0.3);
        border-radius: var(--radius);
    }

    .max-h-60::-webkit-scrollbar-thumb:hover {
        background: hsl(var(--muted-foreground) / 0.5);
    }
</style>

<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        variant?: "primary" | "secondary" | "destructive" | "ghost" | "outline";
        size?: "sm" | "md" | "lg";
        disabled?: boolean;
        onclick?: (event: MouseEvent) => void;
        type?: "button" | "submit" | "reset";
        class?: string;
        children?: Snippet;
        selected?: boolean;
    }

    let {
        variant = "primary",
        size = "md",
        disabled = false,
        onclick,
        type = "button",
        class: className = "",
        children,
        selected = false,
    }: Props = $props();

    // Get variant classes dynamically based on selected state
    const getVariantClasses = $derived(() => {
        if (variant === "outline" && selected) {
            return "bg-primary/10 border border-primary text-primary hover:bg-primary/20";
        }

        const variantClasses = {
            primary:
                "bg-primary text-primary-foreground hover:opacity-90 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0",
            secondary:
                "bg-secondary text-secondary-foreground hover:opacity-80",
            destructive:
                "bg-destructive text-destructive-foreground hover:opacity-90 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0",
            ghost: "bg-transparent text-foreground hover:bg-muted",
            outline:
                "bg-transparent border border-border text-foreground hover:bg-muted hover:border-foreground/30",
        };

        return variantClasses[variant];
    });

    // Size classes
    const sizeClasses = {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
    };

    const buttonClasses = $derived(`
        inline-flex items-center justify-center gap-2 font-medium
        rounded-[var(--radius)] transition-all cursor-pointer
        whitespace-nowrap
        disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
        ${getVariantClasses()}
        ${sizeClasses[size]}
        ${className}
    `);
</script>

<button {type} {disabled} {onclick} class={buttonClasses}>
    {#if children}
        {@render children()}
    {/if}
</button>

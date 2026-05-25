interface Global {
    events: import("./util").EventEmitter,
    theme: "dark" | "light"
}

interface Window {
    EventEmitter: typeof import("./util").EventEmitter
}

declare var global: Global;
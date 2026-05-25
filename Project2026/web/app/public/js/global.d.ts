interface Global {
    [key: string]: never;
}

interface Window {
    global: Global
}

declare var global: Global;
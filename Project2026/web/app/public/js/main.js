import { EventEmitter } from "./util.js";

window.addEventListener("DOMContentLoaded", () => {
    window.global = /** @type {Global} */({
        events: new EventEmitter(),
        theme: "dark"
    });
    window.EventEmitter = EventEmitter;
});

window.addEventListener("load", () => {
    const saved = localStorage.getItem("theme") 
        || (window.matchMedia && (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) 
        || "dark";
    setTheme(/** @type {Global["theme"]} */(saved));

    document.getElementById("themeToggle")?.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        setTheme(current === "dark" ? "light" : "dark");
    });
})

/**
 * 
 * @param {Global["theme"]} theme 
 */
function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    global.theme = theme;
    global.events.emit("setTheme", theme);
}


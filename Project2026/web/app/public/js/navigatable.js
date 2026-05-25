import { rpc } from "./util.js";

//#region ============== Constants ==============
/** @type {HTMLInputElement} */
let searchBar;
//#endregion ============== Constants ==============

//#region ============== Variables ==============
//#endregion ============== Variables ==============

//#region ============== Functions ==============
async function sendSearchQuery() {
    const searchQuery = searchBar.value;
    const query = new URLSearchParams();
    query.set("search", encodeURIComponent(searchQuery));
    await rpc(`/search?${query.toString()}`, {}, { method: "GET" });
}

window.addEventListener("DOMContentLoaded", () => {
    searchBar = /** @type {HTMLInputElement} */(document.getElementById("searchBar"));
    const searchBtn = document.getElementById("searchBtn");

    searchBar?.addEventListener("keydown", async (e) => {
        if (e.key === "Enter") await sendSearchQuery();
    });
    searchBtn?.addEventListener("click", sendSearchQuery);

    
    const query = new URLSearchParams(document.location.search);
    if (searchBar && query.has("search")) searchBar.value = query.get("search") ?? "";
});
//#endregion ============== Functions ==============
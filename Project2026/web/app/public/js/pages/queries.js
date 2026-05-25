import { rpc } from "../util.js";

/**
 * @type {string[]}
 */
let tableClasses;

/**
 * @typedef {Object} QueryResultHead
 * @prop {Array<string>} vars
 */
/**
 * @typedef {Object} QueryResultBinding
 * @prop {string} datatype
 * @prop {string} type
 * @prop {string} value
 */
/**
 * @typedef {Object} QueryResultResult
 * @prop {Array<QueryResultBinding>} bindings
 */
/**
 * @typedef {Object} QueryResult
 * @prop {QueryResultHead} head
 * @prop {QueryResultResult} results
 */

const TABLE = (/** @type {string} */ tag) => {
    const tableEl = document.createElement(tag);
    tableEl.classList.add(tableClasses[0]);
    return tableEl;
}
const TABLE_ELEM = (/** @type {string} */ tag) => {
    const tableEl = document.createElement(tag);
    tableEl.classList.add(...tableClasses);
    return tableEl;
}

/**
 * @param {HTMLDivElement} elem
 * @param {QueryResult} values
 */
function makeTable(elem, values) {
    const tableEl = TABLE("table");
    const theadEl = TABLE("thead");
    const tbodyEl = TABLE("tbody");
    const trEl = TABLE("tr");
    for (const var_ of values.head.vars) {
        const thEl = TABLE("th");
        thEl.innerText = var_;
        trEl.appendChild(thEl);
    }
    theadEl.appendChild(trEl);
    tableEl.appendChild(theadEl);

    for (const bind of values.results.bindings) {
        console.log("BIND:", bind)
        const trEl = TABLE_ELEM("tr");
        for (const var_ of values.head.vars) {
            const tdEl = TABLE_ELEM("td");
            // @ts-ignore
            tdEl.innerText = bind[var_]?.value;
            // @ts-ignore
            tdEl.title = `Tipo: "${bind[var_]?.type}"\nTipo de dados: "${bind[var_]?.datatype}"`
            trEl.appendChild(tdEl);
        }
        tbodyEl.appendChild(trEl);
    }
    tableEl.appendChild(tbodyEl);
    elem.appendChild(tableEl)
}

window.addEventListener("DOMContentLoaded", () => {
    const queryEditor = /** @type {HTMLTextAreaElement} */(document.getElementById("queryEditor"));
    const submitQueryBtn = /** @type {HTMLButtonElement} */(document.getElementById("submitQueryBtn"));
    const queryResults = /** @type {HTMLDivElement} */(document.getElementById("queryResults"));

    submitQueryBtn.addEventListener("click", async () => {
        submitQueryBtn.disabled = true;
        try {
            const res = await rpc("/api/execute", { query: queryEditor.value });
            if (!res.success) throw new Error(res.message);

            console.log("EXECUTE QUERY", res);
            Array.from(queryResults.children).forEach((c) => queryResults.removeChild(c));
            makeTable(queryResults, res.value);
        } catch (e) {
            console.error("Unable to execute query:", e);
        }

        submitQueryBtn.disabled = false;
    });

    // @ts-ignore
    tableClasses = Array.from(document.querySelector("#REMOVE > table > tbody > tr").classList);
    document.getElementById("REMOVE")?.remove();
});
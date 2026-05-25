
/**
 * @callback EventListener
 * @param {string} event
 * @param {...unknown} args
 * @returns {void}
 */
class EventEmitter {
    constructor() {
        /**
         * @type {Record<string, Set<EventListener>>}
         */
        this.listeners = {};
    }

    /**
     * @param {string} event 
     * @param {EventListener} listener 
     */
    on(event, listener) {
        this.listeners[event] ??= new Set();
        this.listeners[event].add(listener);
        return () => this.off(event, listener);
    }

    /**
     * @param {string} event
     * @param {EventListener} listener
     */
    off(event, listener) {
        if (!(event in this.listeners)) return;
        this.listeners[event].delete(listener);
    }

    /**
     * @param {string} event
     * @param {unknown[]} args
     */
    emit(event, ...args) {
        if (!(event in this.listeners)) return;
        for (const listener of this.listeners[event]) {
            listener(event, ...args);
        }
    }
}

/**
 * @param {string} path
 * @param {Record<string, unknown>} body
 * @param {{ method?: "GET" | "POST", json?: boolean }} [options]
 */
async function rpc(path, body, options) {
    const options_ = { ...{ method: "POST", json: true }, ...options }
    return new Promise(async (resolve, reject) => {
        try {
            const res = await fetch(path, {
                headers: {
                    "Content-Type": "application/json"                    
                },
                method: options_.method,
                body: options_.method === "POST" ? JSON.stringify(body) : undefined
            });
            
            if (!res.ok) reject(await res.text());
            if (res.redirected) return resolve(undefined);
            if (!options_.json) return resolve(await res.text());
            resolve(await res.json());
        } catch (e) {
            reject(e);
        }
    });
}

export { EventEmitter, rpc };

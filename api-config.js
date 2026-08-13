(() => {
    const localHosts = ["localhost", "127.0.0.1", "::1"];
    const isLocalPage = window.location.protocol === "file:" || localHosts.includes(window.location.hostname);
    
    // In production (Vercel/GitHub Pages), use current page origin
    const deployedApiOrigin = window.location.origin && window.location.origin !== "null"
        ? window.location.origin
        : "https://hacker-drab-mu.vercel.app";

    const apiOrigin = isLocalPage ? "http://127.0.0.1:8800" : deployedApiOrigin;

    window.AUTOHIRE_API_ORIGIN = apiOrigin;
    window.AUTOHIRE_FASTAPI_ORIGIN = isLocalPage ? "http://127.0.0.1:5501" : apiOrigin;
    window.AUTOHIRE_API_URL = `${apiOrigin}/api/auth`;
})();


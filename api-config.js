(() => {
    const localHosts = ["localhost", "127.0.0.1", "::1"];
    const isLocalPage = localHosts.includes(window.location.hostname);
    const deployedApiOrigin = "https://YOUR-VERCEL-APP.vercel.app";
    const apiOrigin = window.location.protocol === "file:" || isLocalPage
        ? "http://localhost:8800"
        : deployedApiOrigin;

    window.AUTOHIRE_API_ORIGIN = apiOrigin;
    window.AUTOHIRE_API_URL = `${apiOrigin}/api/auth`;
})();

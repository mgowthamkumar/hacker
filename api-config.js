(() => {
    const hostname = window.location.hostname || "127.0.0.1";
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    
    // Determine the IP or hostname of the server for local WiFi / Mobile network support
    const serverHost = (hostname === "" || hostname === "null") ? "127.0.0.1" : hostname;

    let apiOrigin;
    let fastApiOrigin;
    let analyzerOrigin;

    if (window.location.protocol === "file:") {
        apiOrigin = "http://127.0.0.1:8800";
        fastApiOrigin = "http://127.0.0.1:5501";
        analyzerOrigin = "http://127.0.0.1:5503";
    } else if (window.location.port === "8800" || window.location.port === "5503" || window.location.port === "5501" || hostname.match(/^192\.168\./) || hostname.match(/^10\./) || hostname.match(/^172\.(1[6-9]|2[0-9]|3[0-1])\./) || hostname === "localhost" || hostname === "127.0.0.1") {
        apiOrigin = `${protocol}//${serverHost}:8800`;
        fastApiOrigin = `${protocol}//${serverHost}:5501`;
        analyzerOrigin = `${protocol}//${serverHost}:5503`;
    } else {
        const fallbackOrigin = window.location.origin && window.location.origin !== "null" ? window.location.origin : "https://hacker-drab-mu.vercel.app";
        apiOrigin = fallbackOrigin;
        fastApiOrigin = fallbackOrigin;
        analyzerOrigin = fallbackOrigin;
    }

    window.AUTOHIRE_API_ORIGIN = apiOrigin;
    window.AUTOHIRE_FASTAPI_ORIGIN = fastApiOrigin;
    window.AUTOHIRE_ANALYZER_ORIGIN = analyzerOrigin;
    window.AUTOHIRE_API_URL = `${apiOrigin}/api/auth`;
})();

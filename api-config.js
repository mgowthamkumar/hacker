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

    // Global Permanent Google Sign-In & Account Switcher Auth Handler
    window.AutoHireAuth = {
        getUser() {
            try {
                const raw = localStorage.getItem("autoHireProfile") || localStorage.getItem("loggedInUser");
                if (!raw) return null;
                const parsed = JSON.parse(raw);
                return parsed.user || parsed.profile || parsed;
            } catch (e) {
                return null;
            }
        },

        getGoogleSvg() {
            return `<svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>`;
        },

        saveUser(userObj, profileObj) {
            if (!userObj) return;
            const u = {
                id: userObj.id || userObj.sub || Date.now().toString(),
                name: userObj.name || userObj.fullName || (userObj.email ? userObj.email.split("@")[0] : "User"),
                email: (userObj.email || userObj.emailAddress || "").toLowerCase(),
                picture: userObj.picture || userObj.userAvatar || userObj.profilePic || localStorage.getItem("userAvatar") || localStorage.getItem("profilePic") || "",
                provider: userObj.provider || "google"
            };
            const p = profileObj || {
                fullName: u.name,
                emailAddress: u.email,
                picture: u.picture
            };
            localStorage.setItem("loggedInUser", JSON.stringify(u));
            localStorage.setItem("autoHireProfile", JSON.stringify(p));
            if (u.picture) {
                localStorage.setItem("userAvatar", u.picture);
                localStorage.setItem("profilePic", u.picture);
            }
            if (u.name) {
                localStorage.setItem("username", u.name);
                localStorage.setItem("user", u.name);
            }
        },

        async logout(switchAccount = false) {
            try {
                if (window.google && window.google.accounts && window.google.accounts.id) {
                    window.google.accounts.id.disableAutoSelect();
                }
            } catch(e) {}

            const apiUrl = window.AUTOHIRE_API_URL || `${window.AUTOHIRE_API_ORIGIN}/api/auth`;
            try {
                await fetch(`${apiUrl}/logout`, { method: "POST", credentials: "include" });
            } catch(e) {}

            localStorage.removeItem("loggedInUser");
            localStorage.removeItem("autoHireProfile");
            localStorage.removeItem("userAvatar");
            localStorage.removeItem("profilePic");
            localStorage.removeItem("username");
            localStorage.removeItem("user");

            window.location.href = switchAccount ? "sign-in.html?switch=true" : "sign-in.html";
        },

        initHeader() {
            const signInLink = document.getElementById("signInLink");
            const createProfileLink = document.getElementById("createProfileLink");
            const accountButton = document.getElementById("accountButton") || document.getElementById("profile-logo-btn");
            const accountLogo = document.getElementById("accountLogo");
            const accountName = document.getElementById("accountName");
            const accountEmail = document.getElementById("accountEmail");
            const profileCard = document.getElementById("profileCard");
            const profileDetails = document.getElementById("profileDetails");
            const profileFullName = document.getElementById("profileFullName");
            const profileEmail = document.getElementById("profileEmail");
            const logoutButton = document.getElementById("logoutButton") || document.getElementById("logout-link");
            const switchAccountBtn = document.getElementById("switchAccountBtn");

            const user = this.getUser();

            if (user && (user.name || user.email || user.fullName)) {
                const email = user.email || user.emailAddress || "";
                const name = user.name || user.fullName || (email ? email.split("@")[0] : "User");
                const picture = user.picture || user.userAvatar || user.profilePic || localStorage.getItem("userAvatar") || localStorage.getItem("profilePic") || "";

                if (accountLogo) {
                    if (picture) {
                        const img = document.createElement("img");
                        img.src = picture;
                        img.alt = "Google Profile";
                        img.style.cssText = "width:100%;height:100%;object-fit:cover;border-radius:50%;";
                        img.onerror = () => { accountLogo.innerHTML = this.getGoogleSvg(); };
                        accountLogo.innerHTML = "";
                        accountLogo.appendChild(img);
                    } else {
                        accountLogo.innerHTML = this.getGoogleSvg();
                    }
                }
                if (accountName) accountName.textContent = name;
                if (accountEmail) accountEmail.textContent = email;
                if (profileFullName) profileFullName.textContent = name;
                if (profileEmail) profileEmail.textContent = email;

                if (signInLink) signInLink.style.display = "none";
                if (createProfileLink) createProfileLink.style.display = "none";
                if (accountButton) accountButton.classList.add("visible");
                if (profileCard) profileCard.classList.add("visible");
            }

            if (accountButton && profileDetails) {
                accountButton.addEventListener("click", (e) => {
                    e.stopPropagation();
                    const isOpen = !profileDetails.hidden;
                    profileDetails.hidden = isOpen;
                    accountButton.setAttribute("aria-expanded", String(!isOpen));
                });
                document.addEventListener("click", (e) => {
                    if (profileCard && !profileCard.contains(e.target)) {
                        profileDetails.hidden = true;
                        accountButton.setAttribute("aria-expanded", "false");
                    }
                });
            }

            if (logoutButton) {
                logoutButton.addEventListener("click", (e) => {
                    e.preventDefault();
                    this.logout(false);
                });
            }

            if (switchAccountBtn) {
                switchAccountBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    this.logout(true);
                });
            }
        }
    };
})();

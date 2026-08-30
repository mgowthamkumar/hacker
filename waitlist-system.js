/**
 * AutoHire Waitlist & Web Push Notification System
 * Manages FIFO Waitlist Queue, 24-Hour Expiry Logic, Web Push Service Worker,
 * Permission Prompts, and Header Notification Bell Inbox UI.
 */
(() => {
    const WAITLIST_KEY = "autoHireWaitlist";
    const INBOX_KEY = "autoHireNotificationsInbox";
    const SW_PATH = "sw.js";

    class WaitlistSystem {
        constructor() {
            this.swRegistration = null;
            this.initServiceWorker();
        }

        // 1. Service Worker & Push Notification Permission Setup
        async initServiceWorker() {
            if ("serviceWorker" in navigator) {
                try {
                    this.swRegistration = await navigator.serviceWorker.register(SW_PATH);
                } catch (err) {
                    console.warn("AutoHire SW registration notice:", err);
                }
            }
        }

        async requestPermission() {
            if ("Notification" in window) {
                if (Notification.permission === "default") {
                    try {
                        const permission = await Notification.requestPermission();
                        return permission === "granted";
                    } catch (e) {
                        return false;
                    }
                }
                return Notification.permission === "granted";
            }
            return false;
        }

        // 2. Data Store Helpers
        getWaitlist() {
            try {
                return JSON.parse(localStorage.getItem(WAITLIST_KEY) || "[]");
            } catch (e) {
                return [];
            }
        }

        saveWaitlist(list) {
            localStorage.setItem(WAITLIST_KEY, JSON.stringify(list));
        }

        getInbox() {
            try {
                return JSON.parse(localStorage.getItem(INBOX_KEY) || "[]");
            } catch (e) {
                return [];
            }
        }

        saveInbox(inbox) {
            localStorage.setItem(INBOX_KEY, JSON.stringify(inbox));
            this.updateBellBadge();
        }

        // 3. User Helper
        getCurrentUser() {
            if (window.AutoHireAuth) {
                const u = window.AutoHireAuth.getUser();
                if (u) return u;
            }
            try {
                const raw = localStorage.getItem("autoHireProfile") || localStorage.getItem("loggedInUser");
                if (!raw) return null;
                const p = JSON.parse(raw);
                return p.user || p.profile || p;
            } catch (e) {
                return null;
            }
        }

        // 4. Join Waitlist Feature
        joinWaitlist(job) {
            const user = this.getCurrentUser();
            if (!user) {
                alert("⚠️ Please sign in to join the job waitlist!");
                window.location.href = "sign-in.html";
                return null;
            }

            const userId = user.id || user.email || "user_" + Date.now();
            const userName = user.name || user.fullName || user.email || "Applicant";
            const userEmail = (user.email || user.emailAddress || "").toLowerCase();
            const jobId = job.jobId || job.title.replace(/\s+/g, '_').toLowerCase();

            const waitlist = this.getWaitlist();

            // Check if already in waitlist for this job
            const existing = waitlist.find(w => w.userId === userId && w.jobId === jobId && (w.status === "waiting" || w.status === "notified"));
            if (existing) {
                if (existing.status === "waiting") {
                    alert(`ℹ️ You are already in the waitlist for "${job.title}". Position in line: #${this.getQueuePosition(jobId, userId)}.`);
                } else if (existing.status === "notified") {
                    alert(`🎉 A slot is currently open for you for "${job.title}"! Please apply within 24 hours.`);
                }
                return existing;
            }

            const entry = {
                id: "wl_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4),
                userId,
                userName,
                userEmail,
                jobId,
                jobTitle: job.title || "Software Engineering Role",
                company: job.company || "AutoHire Partner",
                joinedAt: Date.now(),
                status: "waiting",
                notifiedAt: null,
                expiresAt: null
            };

            waitlist.push(entry);
            this.saveWaitlist(waitlist);

            // Request push permission on first waitlist action if default
            this.requestPermission();

            const queuePos = this.getQueuePosition(jobId, userId);
            alert(`✅ Added to Waitlist for "${entry.jobTitle}" at ${entry.company}!\n\nPosition in queue: #${queuePos}.\nYou will receive a push notification and inbox alert as soon as a slot opens up.`);

            return entry;
        }

        getQueuePosition(jobId, userId) {
            const list = this.getWaitlist()
                .filter(w => w.jobId === jobId && w.status === "waiting")
                .sort((a, b) => a.joinedAt - b.joinedAt);
            const index = list.findIndex(w => w.userId === userId);
            return index >= 0 ? index + 1 : list.length + 1;
        }

        isUserInWaitlist(jobId) {
            const user = this.getCurrentUser();
            if (!user) return false;
            const userId = user.id || user.email;
            const waitlist = this.getWaitlist();
            return waitlist.some(w => w.userId === userId && w.jobId === jobId && (w.status === "waiting" || w.status === "notified"));
        }

        // 5. Expiry Check & Backend Event Trigger (FIFO Queue)
        checkExpirations() {
            const waitlist = this.getWaitlist();
            const now = Date.now();
            let updated = false;

            waitlist.forEach(entry => {
                if (entry.status === "notified" && entry.expiresAt && now > entry.expiresAt) {
                    entry.status = "expired";
                    updated = true;
                    // Auto-trigger next user in FIFO queue for this jobId
                    setTimeout(() => this.triggerNextNotification(entry.jobId), 100);
                }
            });

            if (updated) {
                this.saveWaitlist(waitlist);
            }
        }

        freeUpSlot(jobId, jobTitleCustom, companyCustom) {
            return this.triggerNextNotification(jobId, jobTitleCustom, companyCustom);
        }

        triggerNextNotification(jobId, jobTitleCustom, companyCustom) {
            this.checkExpirations();

            const waitlist = this.getWaitlist();
            // Find next user in line (FIFO: lowest joinedAt)
            const waitingEntries = waitlist
                .filter(w => w.jobId === jobId && w.status === "waiting")
                .sort((a, b) => a.joinedAt - b.joinedAt);

            if (waitingEntries.length === 0) {
                return null;
            }

            const nextInLine = waitingEntries[0];
            const now = Date.now();
            const expiresAt = now + (24 * 60 * 60 * 1000); // 24 hours expiry

            nextInLine.status = "notified";
            nextInLine.notifiedAt = now;
            nextInLine.expiresAt = expiresAt;

            this.saveWaitlist(waitlist);

            const jobTitle = nextInLine.jobTitle || jobTitleCustom || "Opportunity";
            const company = nextInLine.company || companyCustom || "Company";

            const notificationPayload = {
                title: "A spot opened up!",
                body: `${jobTitle} at ${company} has a free slot. Apply now.`,
                jobId: jobId,
                url: "chatbot.html"
            };

            // 1. Send Web Push Notification
            this.dispatchPushNotification(notificationPayload);

            // 2. Add to Notifications Inbox
            this.addNotificationToInbox({
                id: "notif_" + Date.now(),
                userId: nextInLine.userId,
                title: notificationPayload.title,
                body: notificationPayload.body,
                jobId: jobId,
                jobTitle: jobTitle,
                company: company,
                timestamp: now,
                expiresAt: expiresAt,
                read: false
            });

            return nextInLine;
        }

        dispatchPushNotification(payload) {
            if ("Notification" in window && Notification.permission === "granted") {
                if (navigator.serviceWorker && navigator.serviceWorker.controller) {
                    navigator.serviceWorker.ready.then(reg => {
                        reg.showNotification(payload.title, {
                            body: payload.body,
                            icon: 'background.png.jpeg',
                            badge: 'background.png.jpeg',
                            data: { url: 'chatbot.html', jobId: payload.jobId },
                            vibrate: [200, 100, 200]
                        });
                    }).catch(() => {
                        new Notification(payload.title, { body: payload.body });
                    });
                } else {
                    new Notification(payload.title, { body: payload.body });
                }
            }
        }

        addNotificationToInbox(item) {
            const inbox = this.getInbox();
            inbox.unshift(item);
            this.saveInbox(inbox);
        }

        markAllAsRead() {
            const inbox = this.getInbox();
            inbox.forEach(n => n.read = true);
            this.saveInbox(inbox);
        }

        // 6. Header Bell Icon & Notifications Inbox UI Renderer
        initHeaderBellUI() {
            if (document.getElementById("autohire-bell-container")) return;

            const navActions = document.querySelector(".nav-actions") || document.querySelector(".auth-links");
            if (!navActions) return;

            const bellContainer = document.createElement("div");
            bellContainer.id = "autohire-bell-container";
            bellContainer.style.cssText = "position:relative; display:inline-flex; align-items:center; margin-right:6px;";

            const bellBtn = document.createElement("button");
            bellBtn.id = "autohire-bell-btn";
            bellBtn.type = "button";
            bellBtn.setAttribute("aria-label", "Notifications");
            bellBtn.style.cssText = "background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); color:#f8fafc; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:1.1rem; position:relative; backdrop-filter:blur(10px); transition:all 0.2s;";

            bellBtn.innerHTML = `🔔<span id="autohire-bell-badge" style="display:none; position:absolute; top:-2px; right:-2px; background:#ef4444; color:#fff; font-size:0.7rem; font-weight:800; width:18px; height:18px; border-radius:50%; align-items:center; justify-content:center; border:2px solid #070b14;">0</span>`;

            const dropdown = document.createElement("div");
            dropdown.id = "autohire-inbox-dropdown";
            dropdown.style.cssText = "display:none; position:absolute; top:calc(100% + 12px); right:0; width:320px; max-height:420px; overflow-y:auto; background:rgba(15,23,42,0.96); border:1px solid rgba(255,255,255,0.15); border-radius:16px; padding:16px; backdrop-filter:blur(24px); box-shadow:0 20px 40px rgba(0,0,0,0.6); z-index:9999;";

            bellContainer.appendChild(bellBtn);
            bellContainer.appendChild(dropdown);

            // Insert before profile dropdown/card or at start of actions
            const profileCard = document.getElementById("profileCard") || document.getElementById("profile-logo-btn");
            if (profileCard && profileCard.parentNode === navActions) {
                navActions.insertBefore(bellContainer, profileCard);
            } else {
                navActions.appendChild(bellContainer);
            }

            bellBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                const isHidden = dropdown.style.display === "none";
                dropdown.style.display = isHidden ? "block" : "none";
                if (isHidden) {
                    this.renderInboxList();
                    this.markAllAsRead();
                }
            });

            document.addEventListener("click", (e) => {
                if (!bellContainer.contains(e.target)) {
                    dropdown.style.display = "none";
                }
            });

            this.updateBellBadge();
        }

        updateBellBadge() {
            const badge = document.getElementById("autohire-bell-badge");
            if (!badge) return;
            const inbox = this.getInbox();
            const unreadCount = inbox.filter(n => !n.read).length;

            if (unreadCount > 0) {
                badge.innerText = unreadCount > 9 ? "9+" : unreadCount;
                badge.style.display = "flex";
            } else {
                badge.style.display = "none";
            }
        }

        renderInboxList() {
            const dropdown = document.getElementById("autohire-inbox-dropdown");
            if (!dropdown) return;

            const inbox = this.getInbox();

            if (inbox.length === 0) {
                dropdown.innerHTML = `
                    <div style="text-align:center; padding:20px; color:#94a3b8; font-size:0.9rem;">
                        🔔 No notifications yet.<br><span style="font-size:0.8rem; color:#64748b;">Join a job waitlist to get instant free-slot alerts!</span>
                    </div>
                `;
                return;
            }

            let html = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1);">
                    <strong style="font-family:'Space Grotesk',sans-serif; font-size:1rem; color:#f8fafc;">Notifications Inbox</strong>
                    <span style="font-size:0.75rem; color:#38bdf8; cursor:pointer;" onclick="window.AutoHireWaitlist.markAllAsRead()">Clear Unread</span>
                </div>
                <div style="display:flex; flex-direction:column; gap:10px;">
            `;

            inbox.forEach(item => {
                const timeAgo = this.formatTimeAgo(item.timestamp);
                html += `
                    <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:12px; display:flex; flex-direction:column; gap:4px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; font-size:0.88rem; color:#38bdf8;">${item.title}</span>
                            <span style="font-size:0.7rem; color:#94a3b8;">${timeAgo}</span>
                        </div>
                        <p style="font-size:0.82rem; color:#cbd5e1; margin:2px 0;">${item.body}</p>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                            <span style="font-size:0.72rem; color:#eab308; font-weight:600;">⏳ 24h Slot Active</span>
                            <a href="chatbot.html" style="font-size:0.78rem; font-weight:700; color:#22c55e; text-decoration:none;">Apply Now →</a>
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
            dropdown.innerHTML = html;
        }

        formatTimeAgo(timestamp) {
            const diff = Math.floor((Date.now() - timestamp) / 1000);
            if (diff < 60) return "Just now";
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            return `${Math.floor(diff / 86400)}d ago`;
        }
    }

    window.AutoHireWaitlist = new WaitlistSystem();

    // Auto initialize bell UI when DOM is ready
    window.addEventListener("DOMContentLoaded", () => {
        window.AutoHireWaitlist.initHeaderBellUI();
        window.AutoHireWaitlist.checkExpirations();
    });
})();

/**
 * AutoHire Device Fingerprinting, OTP Verification & Trusted Devices System
 * Features:
 * 1. Device Fingerprinting (User-Agent + OS + Resolution + Language hash)
 * 2. New-Device Detection on Login
 * 3. 6-Digit OTP Generation with 5-Minute TTL
 * 4. Rate-Limiting (Max 3 OTP requests per 10 minutes)
 * 5. Interactive Cyber-Glass 3D OTP Verification Modal
 * 6. Trusted Devices Management Dashboard in Profile Settings
 */
(() => {
    const TRUSTED_DEVICES_KEY_PREFIX = "autoHireTrustedDevices_";
    const OTP_KEY_PREFIX = "autoHireOtp_";
    const OTP_RATE_LIMIT_PREFIX = "autoHireOtpRate_";

    class DeviceAuthSystem {
        constructor() {
            this.fingerprint = this.generateFingerprint();
            this.deviceName = this.getDeviceName();
        }

        // 1. Device Fingerprinting Hash Engine
        generateFingerprint() {
            const raw = [
                navigator.userAgent || "",
                navigator.platform || "",
                screen.width + "x" + screen.height,
                screen.colorDepth || 24,
                navigator.language || "en-US",
                new Date().getTimezoneOffset()
            ].join("|");

            // Simple fast hash string generator
            let hash = 0;
            for (let i = 0; i < raw.length; i++) {
                const char = raw.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash |= 0;
            }
            return "fp_" + Math.abs(hash).toString(36) + "_" + (screen.width * screen.height);
        }

        getDeviceName() {
            const ua = navigator.userAgent;
            let os = "Desktop";
            if (ua.includes("Win")) os = "Windows";
            else if (ua.includes("Mac")) os = "macOS";
            else if (ua.includes("Linux")) os = "Linux";
            else if (ua.includes("Android")) os = "Android Mobile";
            else if (ua.includes("iPhone") || ua.includes("iPad")) os = "iOS Device";

            let browser = "Browser";
            if (ua.includes("Chrome")) browser = "Chrome";
            else if (ua.includes("Firefox")) browser = "Firefox";
            else if (ua.includes("Safari") && !ua.includes("Chrome")) browser = "Safari";
            else if (ua.includes("Edg")) browser = "Edge";

            return `${browser} on ${os} (${screen.width}x${screen.height})`;
        }

        // 2. Trusted Devices Data Store
        getTrustedDevices(userId) {
            try {
                const key = TRUSTED_DEVICES_KEY_PREFIX + (userId || "default");
                return JSON.parse(localStorage.getItem(key) || "[]");
            } catch (e) {
                return [];
            }
        }

        saveTrustedDevices(userId, list) {
            const key = TRUSTED_DEVICES_KEY_PREFIX + (userId || "default");
            localStorage.setItem(key, JSON.stringify(list));
        }

        isDeviceTrusted(userId, fingerprintOverride) {
            const fp = fingerprintOverride || this.fingerprint;
            const list = this.getTrustedDevices(userId);
            return list.some(d => d.fingerprint === fp);
        }

        addTrustedDevice(userId) {
            const list = this.getTrustedDevices(userId);
            const fp = this.fingerprint;

            const existingIndex = list.findIndex(d => d.fingerprint === fp);
            if (existingIndex >= 0) {
                list[existingIndex].lastLoginAt = Date.now();
            } else {
                list.push({
                    id: "dev_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4),
                    deviceName: this.deviceName,
                    fingerprint: fp,
                    createdAt: Date.now(),
                    lastLoginAt: Date.now(),
                    ip: "127.0.0.1 (Local / Mobile Net)"
                });
            }
            this.saveTrustedDevices(userId, list);
        }

        revokeDevice(userId, deviceId) {
            let list = this.getTrustedDevices(userId);
            list = list.filter(d => d.id !== deviceId);
            this.saveTrustedDevices(userId, list);
            this.renderTrustedDevicesSection();
            alert("🔒 Device access revoked successfully!");
        }

        // 3. OTP Engine with 5-Minute TTL and Rate Limiter (Max 3 per 10 mins)
        canRequestOtp(userId) {
            const rateKey = OTP_RATE_LIMIT_PREFIX + (userId || "default");
            let requests = [];
            try {
                requests = JSON.parse(localStorage.getItem(rateKey) || "[]");
            } catch (e) {}

            const tenMinsAgo = Date.now() - (10 * 60 * 1000);
            requests = requests.filter(ts => ts > tenMinsAgo);

            if (requests.length >= 3) {
                return { allowed: false, error: "⚠️ Rate limit reached (Max 3 OTP requests per 10 minutes). Please wait a few minutes before trying again." };
            }

            requests.push(Date.now());
            localStorage.setItem(rateKey, JSON.stringify(requests));
            return { allowed: true };
        }

        generateOtp(userId) {
            const check = this.canRequestOtp(userId);
            if (!check.allowed) {
                return { error: check.error };
            }

            // Generate 6-digit numeric OTP
            const code = Math.floor(100000 + Math.random() * 900000).toString();
            const otpData = {
                code,
                createdAt: Date.now(),
                expiresAt: Date.now() + (5 * 60 * 1000) // 5 minutes TTL
            };

            const otpKey = OTP_KEY_PREFIX + (userId || "default");
            localStorage.setItem(otpKey, JSON.stringify(otpData));

            // Notify Web Push & Console for testing demo
            if (window.AutoHireWaitlist && typeof window.AutoHireWaitlist.dispatchPushNotification === "function") {
                window.AutoHireWaitlist.dispatchPushNotification({
                    title: "🔒 AutoHire Security OTP",
                    body: `Your login verification code is ${code}. Valid for 5 minutes.`,
                    jobId: "security_otp"
                });
            }

            return { success: true, code, expiresAt: otpData.expiresAt };
        }

        verifyOtp(userId, inputCode) {
            const otpKey = OTP_KEY_PREFIX + (userId || "default");
            let otpData = null;
            try {
                otpData = JSON.parse(localStorage.getItem(otpKey));
            } catch (e) {}

            if (!otpData) {
                return { success: false, error: "No active OTP found. Please request a new code." };
            }

            if (Date.now() > otpData.expiresAt) {
                localStorage.removeItem(otpKey);
                return { success: false, error: "⚠️ OTP has expired (5-minute limit). Please request a new code." };
            }

            if (inputCode.trim() !== otpData.code) {
                return { success: false, error: "❌ Incorrect OTP code. Please check and try again." };
            }

            // Correct OTP -> Clear OTP & Trust Device
            localStorage.removeItem(otpKey);
            this.addTrustedDevice(userId);

            return { success: true };
        }

        // 4. Interactive Cyber-Glass 3D OTP Verification Modal
        renderOtpModal(pendingUser, onVerifiedCallback) {
            if (document.getElementById("autohire-otp-modal")) return;

            const userId = pendingUser.id || pendingUser.email;
            const otpResult = this.generateOtp(userId);

            if (otpResult.error) {
                alert(otpResult.error);
                return;
            }

            const modalOverlay = document.createElement("div");
            modalOverlay.id = "autohire-otp-modal";
            modalOverlay.style.cssText = "position:fixed; inset:0; z-index:99999; background:rgba(7,11,20,0.85); backdrop-filter:blur(20px); display:flex; align-items:center; justify-content:center; padding:20px;";

            const modalContent = document.createElement("div");
            modalContent.style.cssText = "width:min(440px, 100%); background:rgba(30,41,59,0.9); border:1px solid rgba(255,255,255,0.15); border-radius:24px; padding:36px; box-shadow:0 25px 50px rgba(0,0,0,0.7), 0 0 35px rgba(56,189,248,0.2); backdrop-filter:blur(24px); color:#f8fafc; text-align:center; transform-style:preserve-3d;";

            modalContent.innerHTML = `
                <div style="font-size:2.5rem; margin-bottom:10px;">🔐</div>
                <h2 style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; margin-bottom:8px;">New Device Detected</h2>
                <p style="color:#94a3b8; font-size:0.92rem; line-height:1.5; margin-bottom:20px;">
                    We detected a login attempt from a new device:<br>
                    <strong style="color:#38bdf8;">${this.deviceName}</strong><br><br>
                    Please enter the 6-digit OTP code sent to your email / device to complete login.
                </p>

                <div style="background:rgba(56,189,248,0.12); border:1px dashed rgba(56,189,248,0.4); border-radius:12px; padding:12px; margin-bottom:20px; color:#38bdf8; font-weight:700; font-size:0.9rem;">
                    🔑 DEMO OTP Code: <span id="demoOtpDisplay" style="font-size:1.2rem; letter-spacing:0.1em; color:#fff; background:rgba(0,0,0,0.3); padding:2px 8px; border-radius:6px;">${otpResult.code}</span>
                </div>

                <div style="display:flex; justify-content:center; gap:8px; margin-bottom:20px;">
                    <input type="text" maxlength="6" id="otpInputCode" placeholder="••••••" style="width:100%; text-align:center; font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:800; letter-spacing:0.3em; padding:12px; border-radius:14px; border:1px solid rgba(255,255,255,0.2); background:rgba(15,23,42,0.8); color:#38bdf8; outline:none;" autocomplete="off">
                </div>

                <div id="otpTimerDisplay" style="font-size:0.83rem; color:#eab308; font-weight:700; margin-bottom:20px;">⏱️ Code expires in: 05:00</div>

                <div id="otpModalError" style="color:#ef4444; font-size:0.85rem; font-weight:700; min-height:20px; margin-bottom:14px;"></div>

                <div style="display:flex; gap:12px;">
                    <button type="button" id="btnCancelOtp" style="flex:1; padding:14px; border:1px solid rgba(255,255,255,0.15); border-radius:12px; background:rgba(255,255,255,0.05); color:#cbd5e1; font-weight:700; cursor:pointer;">Cancel</button>
                    <button type="button" id="btnVerifyOtp" style="flex:2; padding:14px; border:none; border-radius:12px; background:linear-gradient(135deg, #0284c7, #a855f7); color:#fff; font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1rem; cursor:pointer; box-shadow:0 4px 20px rgba(168,85,247,0.4);">Verify & Complete Login</button>
                </div>

                <div style="margin-top:16px;">
                    <button type="button" id="btnResendOtp" style="background:none; border:none; color:#38bdf8; font-size:0.82rem; font-weight:700; cursor:pointer; text-decoration:underline;">Resend Code (Max 3 / 10 mins)</button>
                </div>
            `;

            modalOverlay.appendChild(modalContent);
            document.body.appendChild(modalOverlay);

            const otpInput = document.getElementById("otpInputCode");
            const btnVerify = document.getElementById("btnVerifyOtp");
            const btnCancel = document.getElementById("btnCancelOtp");
            const btnResend = document.getElementById("btnResendOtp");
            const errorDisplay = document.getElementById("otpModalError");
            const timerDisplay = document.getElementById("otpTimerDisplay");
            const demoDisplay = document.getElementById("demoOtpDisplay");

            otpInput.focus();

            // 5-Minute Countdown Timer
            let secondsLeft = 300;
            const timerInterval = setInterval(() => {
                secondsLeft--;
                if (secondsLeft <= 0) {
                    clearInterval(timerInterval);
                    timerDisplay.innerText = "⚠️ OTP Expired. Please click Resend Code.";
                    timerDisplay.style.color = "#ef4444";
                } else {
                    const mins = Math.floor(secondsLeft / 60).toString().padStart(2, '0');
                    const secs = (secondsLeft % 60).toString().padStart(2, '0');
                    timerDisplay.innerText = `⏱️ Code expires in: ${mins}:${secs}`;
                }
            }, 1000);

            btnCancel.addEventListener("click", () => {
                clearInterval(timerInterval);
                document.body.removeChild(modalOverlay);
            });

            btnResend.addEventListener("click", () => {
                const resendResult = this.generateOtp(userId);
                if (resendResult.error) {
                    errorDisplay.innerText = resendResult.error;
                } else {
                    errorDisplay.innerText = "";
                    demoDisplay.innerText = resendResult.code;
                    secondsLeft = 300;
                    alert(`✅ New OTP Code generated: ${resendResult.code}`);
                }
            });

            btnVerify.addEventListener("click", () => {
                const code = otpInput.value.trim();
                if (!code) {
                    errorDisplay.innerText = "Please enter the 6-digit verification code.";
                    return;
                }

                const result = this.verifyOtp(userId, code);
                if (result.success) {
                    clearInterval(timerInterval);
                    document.body.removeChild(modalOverlay);
                    if (typeof onVerifiedCallback === "function") {
                        onVerifiedCallback();
                    }
                } else {
                    errorDisplay.innerText = result.error;
                }
            });
        }

        // 5. Trusted Devices Dashboard Renderer for profile.html
        renderTrustedDevicesSection(containerId = "trusted-devices-container") {
            const container = document.getElementById(containerId);
            if (!container) return;

            const currentUser = window.AutoHireAuth ? window.AutoHireAuth.getUser() : null;
            if (!currentUser) {
                container.innerHTML = `<p style="color:#94a3b8; font-size:0.9rem;">Sign in to manage your trusted devices.</p>`;
                return;
            }

            const userId = currentUser.id || currentUser.email;
            const list = this.getTrustedDevices(userId);

            let html = `
                <div style="background:rgba(30,41,59,0.65); border:1px solid rgba(255,255,255,0.12); border-radius:20px; padding:28px; backdrop-filter:blur(16px); box-shadow:0 10px 30px rgba(0,0,0,0.4);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                        <div>
                            <h2 style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; color:#f8fafc;">📱 Trusted Devices</h2>
                            <p style="color:#94a3b8; font-size:0.88rem; margin-top:2px;">Devices that can log in without requiring new-device OTP verification.</p>
                        </div>
                        <span style="padding:6px 14px; border-radius:20px; background:rgba(56,189,248,0.15); color:#38bdf8; font-weight:800; font-size:0.8rem;">${list.length} Active Devices</span>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:12px;">
            `;

            if (list.length === 0) {
                html += `
                    <div style="background:rgba(15,23,42,0.6); padding:16px; border-radius:12px; border:1px dashed rgba(255,255,255,0.1); color:#94a3b8; font-size:0.9rem; text-align:center;">
                        No trusted devices registered yet. Log in on a new device to register it.
                    </div>
                `;
            } else {
                list.forEach(device => {
                    const isCurrent = device.fingerprint === this.fingerprint;
                    const dateStr = new Date(device.lastLoginAt).toLocaleDateString() + " at " + new Date(device.lastLoginAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    html += `
                        <div style="background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:16px; display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap:14px;">
                                <div style="width:42px; height:42px; border-radius:50%; background:rgba(56,189,248,0.15); color:#38bdf8; display:flex; align-items:center; justify-content:center; font-size:1.3rem;">💻</div>
                                <div>
                                    <div style="font-weight:700; font-size:0.95rem; color:#f8fafc; display:flex; align-items:center; gap:8px;">
                                        ${device.deviceName}
                                        ${isCurrent ? '<span style="font-size:0.72rem; padding:2px 8px; border-radius:10px; background:rgba(34,197,94,0.2); color:#4ade80; border:1px solid rgba(34,197,94,0.4);">This Device</span>' : ''}
                                    </div>
                                    <div style="font-size:0.78rem; color:#94a3b8; margin-top:2px;">Last Active: ${dateStr} · IP: ${device.ip}</div>
                                </div>
                            </div>
                            <button type="button" onclick="window.AutoHireDeviceAuth.revokeDevice('${userId}', '${device.id}')" style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#f87171; padding:8px 14px; border-radius:8px; font-weight:700; font-size:0.82rem; cursor:pointer; transition:background 0.2s;">
                                🚫 Revoke Access
                            </button>
                        </div>
                    `;
                });
            }

            html += `
                    </div>
                </div>
            `;

            container.innerHTML = html;
        }
    }

    window.AutoHireDeviceAuth = new DeviceAuthSystem();

    window.addEventListener("DOMContentLoaded", () => {
        window.AutoHireDeviceAuth.renderTrustedDevicesSection();
    });
})();

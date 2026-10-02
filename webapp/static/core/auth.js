(function () {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const input = document.getElementById(button.dataset.passwordToggle);
        if (!input) return;

        button.addEventListener("click", () => {
            const shouldShow = input.type === "password";
            input.type = shouldShow ? "text" : "password";
            button.textContent = shouldShow ? "Hide" : "Show";
            button.setAttribute("aria-pressed", String(shouldShow));
        });
    });

    const password = document.getElementById("id_password1");
    const meter = document.querySelector("[data-password-strength] .strength-meter");
    const fill = document.querySelector("[data-password-strength] .strength-meter-fill");
    const label = document.getElementById("password-strength-label");
    if (!password || !meter || !fill || !label) return;

    const username = document.getElementById("id_username");
    const strengthNames = ["Enter a password", "Very weak", "Weak", "Fair", "Good", "Strong"];

    function updateStrength() {
        const value = password.value;
        if (!value) {
            meter.setAttribute("aria-valuenow", "0");
            meter.setAttribute("aria-valuetext", "No password entered");
            fill.style.width = "0%";
            fill.dataset.level = "0";
            label.textContent = strengthNames[0];
            return;
        }

        const checks = [
            value.length >= 8,
            value.length >= 12,
            /[a-z]/.test(value) && /[A-Z]/.test(value),
            /\d/.test(value),
            /[^A-Za-z0-9]/.test(value),
        ];
        let score = checks.filter(Boolean).length;
        if (/^\d+$/.test(value)) score = Math.min(score, 1);
        const usernameValue = username ? username.value.trim().toLowerCase() : "";
        if (usernameValue.length >= 3 && value.toLowerCase().includes(usernameValue)) {
            score = Math.max(0, score - 1);
        }

        const strength = strengthNames[score];
        meter.setAttribute("aria-valuenow", String(score));
        meter.setAttribute("aria-valuetext", strength);
        fill.style.width = `${score * 20}%`;
        fill.dataset.level = String(score);
        label.textContent = strength;
    }

    password.addEventListener("input", updateStrength);
    if (username) username.addEventListener("input", updateStrength);
    updateStrength();
}());

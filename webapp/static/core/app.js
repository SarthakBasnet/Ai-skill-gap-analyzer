(function () {
    const form = document.getElementById("analysis-form");
    const skillsList = document.getElementById("skills-list");
    const addSkillButton = document.getElementById("add-skill");
    const analyzeButton = document.getElementById("analyze-button");
    const buttonLabel = analyzeButton.querySelector(".button-label");
    const formHint = document.getElementById("form-hint");
    const errorMessage = document.getElementById("error-message");
    const results = document.getElementById("results");
    const unmatched = document.getElementById("unmatched");
    const recommendations = document.getElementById("recommendations");
    let chart;

    function csrfToken() {
        // Django's csrf_token tag sets the cookie; send it in the same-origin header.
        const cookie = document.cookie.split("; ").find((item) => item.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
    }

    function showError(message) { errorMessage.querySelector("span:last-child").textContent = message; errorMessage.hidden = false; }
    function clearError() { errorMessage.hidden = true; errorMessage.querySelector("span:last-child").textContent = ""; }
    function validRows() {
        return [...skillsList.querySelectorAll(".skill-row")].filter((row) => { const name = row.querySelector('[name="skill"]').value.trim(); const level = row.querySelector('[name="level"]').value; return name && level !== "" && Number(level) >= 0 && Number(level) <= 5; });
    }
    function updateValidation() {
        const hasRole = Boolean(document.getElementById("job-title").value);
        const rows = validRows();
        analyzeButton.disabled = !hasRole || !rows.length;
        if (!hasRole) formHint.textContent = "Choose a target role and add at least one skill to continue.";
        else if (!rows.length) formHint.textContent = "Add at least one skill to unlock your analysis.";
        else formHint.textContent = `${rows.length} skill${rows.length === 1 ? "" : "s"} ready to analyze.`;
    }
    function addRow() {
        const index = skillsList.querySelectorAll(".skill-row").length + 1;
        const row = document.createElement("div");
        row.className = "skill-row";
        row.innerHTML = `<div class="skill-input-wrap"><label class="sr-only" for="skill-${index}">Skill ${index}</label><input id="skill-${index}" type="text" name="skill" placeholder="Add another skill" autocomplete="off"></div><div class="level-input-wrap"><label class="sr-only" for="level-${index}">Skill ${index} level, 0 to 5</label><input id="level-${index}" type="number" name="level" min="0" max="5" value="0" inputmode="numeric"><span>/ 5</span></div><button type="button" class="icon-button remove-skill" aria-label="Remove skill ${index}">×</button>`;
        skillsList.appendChild(row); row.querySelector("input").focus(); updateValidation();
    }
    function statusLabel(status) { return status === "met" ? "On track" : status === "partial" ? "Build this" : "Start here"; }

    addSkillButton.addEventListener("click", addRow);
    document.getElementById("job-title").addEventListener("change", updateValidation);
    skillsList.addEventListener("input", updateValidation);
    skillsList.addEventListener("click", (event) => { if (event.target.classList.contains("remove-skill")) { event.target.closest(".skill-row").remove(); updateValidation(); } });

    function renderRecommendations(items, gaps) {
        recommendations.replaceChildren();
        const gapBySkill = Object.fromEntries(gaps.map((gap) => [gap.skill, gap]));
        document.getElementById("recommendation-count").textContent = `${items.length} focus area${items.length === 1 ? "" : "s"}`;
        if (!items.length) { recommendations.innerHTML = '<li class="recommendation met"><div class="recommendation-header"><strong>You\'re in great shape for this role.</strong><span class="status-badge met">On track</span></div></li>'; return; }
        items.forEach((item) => {
            const gap = gapBySkill[item.skill] || { status: "partial" };
            const li = document.createElement("li"); li.className = `recommendation ${gap.status}`;
            const header = document.createElement("div"); header.className = "recommendation-header";
            header.innerHTML = `<div><strong>${item.skill}</strong> <span class="priority">Priority ${item.priority_rank}</span></div><span class="status-badge ${gap.status}">${statusLabel(gap.status)}</span>`;
            li.appendChild(header);
            const resourceList = document.createElement("div"); resourceList.className = "resources";
            item.resources.forEach((resource) => { const link = document.createElement("a"); link.className = "resource-link"; link.href = resource.url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = `${resource.title} ↗`; resourceList.appendChild(link); });
            if (item.resources.length) li.appendChild(resourceList); recommendations.appendChild(li);
        });
    }
    function renderResults(data) {
        document.getElementById("match-percent").textContent = `${data.overall_match_percent}%`;
        document.getElementById("results-summary").textContent = `${data.role_title} — a snapshot of where you are and what to build next.`;
        const labels = data.skill_gaps.map((item) => item.skill);
        const currentColors = data.skill_gaps.map((item) => item.status === "met" ? "#21856d" : item.status === "missing" ? "#dc5a57" : "#c58a24");
        if (chart) chart.destroy();
        chart = new Chart(document.getElementById("skill-chart"), { type: "bar", data: { labels, datasets: [{ label: "Required level", data: data.skill_gaps.map((item) => item.required_level), backgroundColor: "#cbd3e5", borderRadius: 5, barPercentage: .8 }, { label: "Your level", data: data.skill_gaps.map((item) => item.user_level), backgroundColor: currentColors, borderRadius: 5, barPercentage: .8 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.raw}/5` } } }, scales: { x: { grid: { display: false }, ticks: { color: "#66728b", font: { family: "DM Sans" } } }, y: { beginAtZero: true, max: 5, ticks: { stepSize: 1, color: "#66728b" }, grid: { color: "#edf0f5" } } } } });
        const met = data.skill_gaps.filter((item) => item.status === "met").length;
        document.getElementById("chart-summary").textContent = `${met} of ${data.skill_gaps.length} required skills currently meet the target level. Teal means on-track, amber means partial, and coral means missing.`;
        if (data.unmatched_inputs.length) { unmatched.querySelector("span:last-child").textContent = `We couldn't confidently match: ${data.unmatched_inputs.join(", ")}. Try a more specific skill phrase.`; unmatched.hidden = false; } else unmatched.hidden = true;
        renderRecommendations(data.recommendations, data.skill_gaps); results.hidden = false; results.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault(); clearError(); updateValidation(); if (analyzeButton.disabled) return;
        const skills = {}; validRows().forEach((row) => { skills[row.querySelector('[name="skill"]').value.trim()] = Number(row.querySelector('[name="level"]').value); });
        analyzeButton.disabled = true; analyzeButton.classList.add("is-loading"); buttonLabel.textContent = "Analyzing your gap...";
        try {
            const response = await fetch("/api/skill-gap/", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() }, body: JSON.stringify({ job_title: document.getElementById("job-title").value, skills }) });
            const data = await response.json(); if (!response.ok) { const details = Object.values(data).flat().join(" "); throw new Error(details || "The analysis could not be completed."); } renderResults(data);
        } catch (error) { showError(error.message || "The analysis could not be completed."); }
        finally { analyzeButton.classList.remove("is-loading"); buttonLabel.textContent = "Analyze my gap"; updateValidation(); }
    });
    updateValidation();
}());

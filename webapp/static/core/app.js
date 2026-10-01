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
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let chart;

    function animateMatchPercent(finalValue) {
        const output = document.getElementById("match-percent");
        if (reduceMotion) { output.textContent = `${finalValue}%`; return; }
        const duration = 1000;
        const start = performance.now();
        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            output.textContent = `${Math.round(finalValue * eased)}%`;
            if (progress < 1) window.requestAnimationFrame(tick);
        }
        window.requestAnimationFrame(tick);
    }

    const apiBase = (window.SKILLBRIDGE_API_URL || "").replace(/\/$/, "");

    function showError(message) { errorMessage.querySelector("span:last-child").textContent = message; errorMessage.hidden = false; }
    function clearError() { errorMessage.hidden = true; errorMessage.querySelector("span:last-child").textContent = ""; }
    function validRows() {
        return [...skillsList.querySelectorAll(".skill-row")].filter((row) => { const name = row.querySelector('[name="skill"]').value.trim(); const level = row.querySelector('[name="level"]').value; return name && level !== "" && [1, 3, 4, 5].includes(Number(level)); });
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
        row.innerHTML = `<div class="skill-input-wrap"><label class="sr-only" for="skill-${index}">Skill ${index}</label><input id="skill-${index}" type="text" name="skill" placeholder="Add another skill" autocomplete="off"></div><div class="level-input-wrap"><label class="sr-only" for="level-${index}">Skill ${index} level</label><select id="level-${index}" name="level"><option value="">Choose level</option><option value="1">Beginner</option><option value="3">Intermediate</option><option value="4">Advanced</option><option value="5">Expert</option></select></div><button type="button" class="icon-button remove-skill" aria-label="Remove skill ${index}">×</button>`;
        skillsList.appendChild(row); row.querySelector("input").focus(); updateValidation();
    }
    function statusLabel(status) { return status === "met" ? "On track" : status === "partial" ? "Build this" : "Start here"; }

    addSkillButton.addEventListener("click", addRow);
    document.getElementById("job-title").addEventListener("change", updateValidation);
    skillsList.addEventListener("input", updateValidation);
    skillsList.addEventListener("change", updateValidation);
    skillsList.addEventListener("click", (event) => { if (event.target.classList.contains("remove-skill")) { event.target.closest(".skill-row").remove(); updateValidation(); } });

    fetch(`${apiBase}/api/roles/`)
        .then((response) => { if (!response.ok) throw new Error("Could not load job roles."); return response.json(); })
        .then((roles) => {
            const selector = document.getElementById("job-title");
            if (selector.options.length > 1) return;
            roles.forEach((role) => {
                const option = document.createElement("option");
                option.value = role.slug;
                option.textContent = role.title;
                selector.appendChild(option);
            });
        })
        .catch(() => showError("Could not connect to the analyzer. Check the API URL and deployment CORS settings."));

    function renderRecommendations(items, gaps) {
        recommendations.replaceChildren();
        const gapBySkill = Object.fromEntries(gaps.map((gap) => [gap.skill, gap]));
        document.getElementById("recommendation-count").textContent = `${items.length} focus area${items.length === 1 ? "" : "s"}`;
        if (!items.length) { recommendations.innerHTML = '<li class="recommendation met"><div class="recommendation-header"><strong>You\'re in great shape for this role.</strong><span class="status-badge met">On track</span></div></li>'; return; }
        items.forEach((item) => {
            const gap = gapBySkill[item.skill] || { status: "partial" };
            const li = document.createElement("li"); li.className = `recommendation ${gap.status}`;
            if (!reduceMotion) {
                const stagger = Math.min(80, 400 / Math.max(items.length, 1));
                li.classList.add("entering"); li.style.animationDelay = `${Math.min((recommendations.children.length) * stagger, 400)}ms`;
            }
            const header = document.createElement("div"); header.className = "recommendation-header";
            header.innerHTML = `<div><strong>${item.skill}</strong> <span class="priority">Priority ${item.priority_rank}</span></div><span class="status-badge ${gap.status}">${statusLabel(gap.status)}</span>`;
            li.appendChild(header);
            const resourceList = document.createElement("div"); resourceList.className = "resources";
            item.resources.forEach((resource) => { const link = document.createElement("a"); link.className = "resource-link"; link.href = resource.url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = `${resource.title} ↗`; resourceList.appendChild(link); });
            if (item.resources.length) li.appendChild(resourceList); recommendations.appendChild(li);
        });
    }
    function renderResults(data) {
        animateMatchPercent(data.overall_match_percent);
        document.getElementById("results-summary").textContent = `${data.role_title} — a snapshot of where you are and what to build next.`;
        const labels = data.skill_gaps.map((item) => item.skill);
        const currentColors = data.skill_gaps.map((item) => item.status === "met" ? "#52663a" : item.status === "missing" ? "#a34f3e" : "#87651f");
        if (chart) chart.destroy();
        const levelLabel = (level) => ({ 0: "None", 1: "Beginner", 3: "Intermediate", 4: "Advanced", 5: "Expert" }[level] || `Level ${level}`);
        chart = new Chart(document.getElementById("skill-chart"), { type: "bar", data: { labels, datasets: [{ label: "Required level", data: data.skill_gaps.map((item) => item.required_level), backgroundColor: "#c8c8b7", borderRadius: 3, barPercentage: .8 }, { label: "Your level", data: data.skill_gaps.map((item) => item.user_level), backgroundColor: currentColors, borderRadius: 3, barPercentage: .8 }] }, options: { animation: { duration: reduceMotion ? 0 : 850, easing: "easeOutQuart" }, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${levelLabel(context.raw)} (${context.raw})` } } }, scales: { x: { grid: { display: false }, ticks: { color: "#5e5b50", font: { family: "Karla" } } }, y: { beginAtZero: true, max: 5, ticks: { stepSize: 1, color: "#5e5b50" }, grid: { color: "#e6e2d6" } } } } });
        const met = data.skill_gaps.filter((item) => item.status === "met").length;
        document.getElementById("chart-summary").textContent = `${met} of ${data.skill_gaps.length} required skills currently meet the target level. Olive means on-track, amber means partial, and rust means missing.`;
        if (data.unmatched_inputs.length) { unmatched.querySelector("span:last-child").textContent = `We couldn't confidently match: ${data.unmatched_inputs.join(", ")}. Try a more specific skill phrase.`; unmatched.hidden = false; } else unmatched.hidden = true;
        renderRecommendations(data.recommendations, data.skill_gaps); results.hidden = false; results.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault(); clearError(); updateValidation(); if (analyzeButton.disabled) return;
        // Blank levels are omitted, so the backend treats those skills as missing (level 0).
        // The selector values already map labels to the API's unchanged integer scale.
        const skills = {}; validRows().forEach((row) => { skills[row.querySelector('[name="skill"]').value.trim()] = Number(row.querySelector('[name="level"]').value); });
        analyzeButton.disabled = true; analyzeButton.classList.add("is-loading"); buttonLabel.textContent = "Analyzing...";
        try {
            const response = await fetch(`${apiBase}/api/skill-gap/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_title: document.getElementById("job-title").value, skills }) });
            const data = await response.json(); if (!response.ok) { const details = Object.values(data).flat().join(" "); throw new Error(details || "The analysis could not be completed."); } renderResults(data);
        } catch (error) { showError(error.message || "The analysis could not be completed."); }
        finally { analyzeButton.classList.remove("is-loading"); buttonLabel.textContent = "Analyze my gap"; updateValidation(); }
    });
    updateValidation();
}());

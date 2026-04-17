const THEME_STORAGE_KEY = "resume_theme";
const rootElement = document.documentElement;
const toggleButton = document.getElementById("themeToggle");

function getCurrentTheme() {
    const activeTheme = rootElement.getAttribute("data-theme");
    if (activeTheme === "light" || activeTheme === "dark") {
        return activeTheme;
    }
    return "dark";
}

function setButtonLabel(theme) {
    if (!toggleButton) {
        return;
    }

    toggleButton.textContent = theme === "light" ? "Switch to Dark" : "Switch to Light";
    toggleButton.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
}

function applyTheme(theme) {
    rootElement.setAttribute("data-theme", theme);
    setButtonLabel(theme);
    try {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (error) {
        // Ignore storage write errors.
    }
}

if (toggleButton) {
    setButtonLabel(getCurrentTheme());
    toggleButton.addEventListener("click", () => {
        const nextTheme = getCurrentTheme() === "light" ? "dark" : "light";
        applyTheme(nextTheme);
    });
}

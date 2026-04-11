const form = document.querySelector("form");
const resumeInput = document.getElementById("resumeInput");
const dropzone = document.getElementById("dropzone");
const pickBtn = document.getElementById("pickFiles");
const clearBtn = document.getElementById("clearFiles");
const fileList = document.getElementById("fileList");
const submitBtn = document.getElementById("submitBtn");
const jobDesc = document.getElementById("jobDescription");
const charCount = document.getElementById("charCount");

const acceptedTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"];

function updateCount() {
    charCount.textContent = `${jobDesc.value.trim().length} characters`;
    refreshSubmitState();
}

function refreshSubmitState() {
    const hasDesc = jobDesc.value.trim().length > 20;
    const hasFiles = resumeInput.files.length > 0;
    submitBtn.disabled = !(hasDesc && hasFiles);
}

function renderFiles() {
    fileList.innerHTML = "";

    if (!resumeInput.files.length) {
        const chip = document.createElement("div");
        chip.className = "file-chip";
        chip.textContent = "No files selected";
        fileList.appendChild(chip);
        return;
    }

    Array.from(resumeInput.files).forEach((file) => {
        const chip = document.createElement("div");
        chip.className = "file-chip";
        chip.textContent = file.name;
        fileList.appendChild(chip);
    });
}

function setFiles(fileListFromDrop) {
    const dt = new DataTransfer();

    Array.from(fileListFromDrop).forEach((file) => {
        const validByType = acceptedTypes.includes(file.type);
        const validByName = /\.(pdf|doc|docx)$/i.test(file.name);

        if (validByType || validByName) {
            dt.items.add(file);
        }
    });

    resumeInput.files = dt.files;
    renderFiles();
    refreshSubmitState();
}

pickBtn.addEventListener("click", () => resumeInput.click());

clearBtn.addEventListener("click", () => {
    resumeInput.value = "";
    renderFiles();
    refreshSubmitState();
});

resumeInput.addEventListener("change", () => {
    renderFiles();
    refreshSubmitState();
});

jobDesc.addEventListener("input", updateCount);

["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("active");
    });
});

["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => {
        dropzone.classList.remove("active");
    });
});

dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    setFiles(event.dataTransfer.files);
});

dropzone.addEventListener("click", () => resumeInput.click());

form.addEventListener("submit", (event) => {
    if (submitBtn.disabled) {
        event.preventDefault();
    }
});

updateCount();
renderFiles();
refreshSubmitState();

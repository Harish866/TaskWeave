document.addEventListener("DOMContentLoaded", () => {
    const startProjectButton = document.getElementById("startProject");
    if (startProjectButton) {
        startProjectButton.addEventListener("click", () => {
            window.location.href = "/workspace/";
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const statusSelect = document.getElementById(
        "security-next-status"
    );

    const resolutionContainer = document.getElementById(
        "security-resolution-input"
    );

    const resolutionTextarea = document.getElementById(
        "security-resolution-notes"
    );

    if (
        !statusSelect ||
        !resolutionContainer ||
        !resolutionTextarea
    ) {
        return;
    }

    function updateResolutionField() {
        const resolving =
            statusSelect.value === "RESOLVED";

        resolutionContainer.hidden = !resolving;
        resolutionTextarea.required = resolving;

        if (!resolving) {
            resolutionTextarea.value = "";
        }
    }

    statusSelect.addEventListener(
        "change",
        updateResolutionField
    );

    updateResolutionField();
});
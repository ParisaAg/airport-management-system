document.addEventListener(
    "DOMContentLoaded",
    function () {
        const statusSelect =
            document.getElementById(
                "passenger-next-status"
            );

        const resolutionBox =
            document.getElementById(
                "passenger-resolution"
            );

        const resolutionNotes =
            document.getElementById(
                "passenger-resolution-notes"
            );

        if (
            !statusSelect ||
            !resolutionBox ||
            !resolutionNotes
        ) {
            return;
        }

        function updateResolution() {
            const completing =
                statusSelect.value
                === "COMPLETED";

            resolutionBox.hidden =
                !completing;

            resolutionNotes.required =
                completing;

            if (!completing) {
                resolutionNotes.value = "";
            }
        }

        statusSelect.addEventListener(
            "change",
            updateResolution
        );

        updateResolution();
    }
);
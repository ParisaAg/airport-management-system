document.addEventListener(
    "DOMContentLoaded",
    function () {
        const prioritySelect =
            document.getElementById(
                "id_priority"
            );

        const priorityPreview =
            document.getElementById(
                "ps-priority-preview"
            );

        const priorityText =
            document.getElementById(
                "ps-priority-text"
            );

        if (
            !prioritySelect ||
            !priorityPreview ||
            !priorityText
        ) {
            return;
        }

        const priorityClasses = [
            "priority-low",
            "priority-medium",
            "priority-high",
            "priority-urgent",
        ];

        const priorityLabels = {
            LOW: "Standard service priority",
            MEDIUM: "Moderate service priority",
            HIGH: "High operational priority",
            URGENT: "Immediate attention required",
        };

        function updatePriorityPreview() {
            priorityClasses.forEach(
                function (className) {
                    priorityPreview.classList.remove(
                        className
                    );
                }
            );

            const value =
                prioritySelect.value;

            if (!value) {
                priorityText.textContent =
                    "Select priority";

                return;
            }

            priorityPreview.classList.add(
                "priority-"
                + value.toLowerCase()
            );

            priorityText.textContent =
                priorityLabels[value]
                || value;
        }

        prioritySelect.addEventListener(
            "change",
            updatePriorityPreview
        );

        updatePriorityPreview();
    }
);
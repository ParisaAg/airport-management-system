"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(
        "[data-flight-status-form]",
    );

    if (!form) {
        return;
    }

    const statusSelect = form.querySelector(
        "[name='status']",
    );

    const delayField = form.querySelector(
        "[data-delay-field]",
    );

    const delayInput = form.querySelector(
        "[name='delay_minutes']",
    );

    const reasonPanel = form.querySelector(
        "[data-reason-panel]",
    );

    const reasonInput = form.querySelector(
        "[name='reason']",
    );

    const reasonLabel = form.querySelector(
        "[data-reason-label]",
    );

    const reasonHelp = form.querySelector(
        "[data-reason-help]",
    );

    const estimatedPreview = form.querySelector(
        "[data-estimated-preview]",
    );

    const estimatedTime = form.querySelector(
        "[data-estimated-time]",
    );

    const scheduledDeparture = new Date(
        form.dataset.scheduledDeparture,
    );

    function updateEstimatedTime() {
        const minutes = Number.parseInt(
            delayInput.value,
            10,
        );

        if (
            Number.isNaN(minutes)
            || Number.isNaN(
                scheduledDeparture.getTime(),
            )
        ) {
            estimatedTime.textContent = "—";
            return;
        }

        const estimated = new Date(
            scheduledDeparture.getTime()
            + minutes * 60 * 1000,
        );

        estimatedTime.textContent = (
            new Intl.DateTimeFormat(
                "en-GB",
                {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                },
            ).format(estimated)
        );
    }

    function updateFields() {
        const status = statusSelect.value;
        const isDelayed = status === "DELAYED";
        const isCancelled = (
            status === "CANCELLED"
        );

        delayField.hidden = !isDelayed;
        reasonPanel.hidden = !(
            isDelayed || isCancelled
        );

        estimatedPreview.hidden = !isDelayed;

        delayInput.required = isDelayed;
        reasonInput.required = (
            isDelayed || isCancelled
        );

        if (isDelayed) {
            reasonLabel.textContent = "Delay reason";
            reasonHelp.textContent = (
                "Explain why the flight is delayed."
            );
        } else if (isCancelled) {
            reasonLabel.textContent = (
                "Cancellation reason"
            );
            reasonHelp.textContent = (
                "This reason will be visible "
                + "to operational users."
            );

            delayInput.value = "";
        } else {
            delayInput.value = "";
            reasonInput.value = "";
        }

        updateEstimatedTime();
    }

    statusSelect.addEventListener(
        "change",
        updateFields,
    );

    delayInput.addEventListener(
        "input",
        updateEstimatedTime,
    );

    updateFields();
});
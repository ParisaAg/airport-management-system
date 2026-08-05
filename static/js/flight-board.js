"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const board = document.querySelector(".flight-board");

    if (!board) {
        return;
    }

    const endpoint = board.dataset.endpoint;
    const airportSelect = document.querySelector("#airport-select");
    const tabs = document.querySelectorAll(".board-tab");
    const refreshButton = document.querySelector("#refresh-board");
    const tableBody = document.querySelector("#flight-board-body");
    const loading = document.querySelector("#board-loading");
    const emptyState = document.querySelector("#board-empty");
    const errorBox = document.querySelector("#board-error");
    const airportHeading = document.querySelector("#airport-heading");
    const boardTypeLabel = document.querySelector("#board-type-label");
    const routeHeading = document.querySelector("#route-heading");
    const lastUpdated = document.querySelector("#last-updated");
    const clockTime = document.querySelector("#board-time");
    const clockDate = document.querySelector("#board-date");

    let boardType = "DEPARTURES";
    let requestController = null;

    function updateClock() {
        const now = new Date();

        clockTime.textContent = new Intl.DateTimeFormat("en-GB", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
        }).format(now);

        clockDate.textContent = new Intl.DateTimeFormat("en-GB", {
            weekday: "long",
            day: "2-digit",
            month: "short",
            year: "numeric",
        }).format(now);
    }

    function formatFlightTime(value) {
        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return { time: "—", date: "" };
        }

        return {
            time: new Intl.DateTimeFormat("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
            }).format(date),
            date: new Intl.DateTimeFormat("en-GB", {
                day: "2-digit",
                month: "short",
            }).format(date),
        };
    }

    function createCell(className = "") {
        const cell = document.createElement("td");
        cell.className = className;
        return cell;
    }

    function createMainAndSecondary(primary, secondary) {
        const wrapper = document.createElement("div");
        wrapper.className = "board-cell-stack";

        const strong = document.createElement("strong");
        strong.textContent = primary || "—";

        const small = document.createElement("small");
        small.textContent = secondary || "";

        wrapper.append(strong, small);
        return wrapper;
    }

    function renderFlight(flight) {
        const row = document.createElement("tr");
        const time = formatFlightTime(
            flight.display_time || flight.scheduled_time,
        );
        const scheduledTime = formatFlightTime(flight.scheduled_time);
        const timeSecondary = flight.delay_minutes > 0
            ? `${time.date} · Scheduled ${scheduledTime.time}`
            : time.date;

        const timeCell = createCell("board-time-cell");
        timeCell.append(createMainAndSecondary(time.time, timeSecondary));

        if (flight.delay_minutes > 0) {
            const delayLabel = document.createElement("span");
            delayLabel.className = "board-delay-label";
            delayLabel.textContent = `+${flight.delay_minutes} min`;
            timeCell.append(delayLabel);
        }

        const flightCell = createCell();
        flightCell.append(createMainAndSecondary(
            flight.flight_number,
            flight.airline.iata_code,
        ));

        const airlineCell = createCell();
        airlineCell.textContent = flight.airline.name;

        const route = boardType === "ARRIVALS"
            ? flight.origin
            : flight.destination;

        const routeCell = createCell();
        routeCell.append(createMainAndSecondary(
            route.iata_code,
            route.city,
        ));

        const terminalCell = createCell();
        terminalCell.textContent = flight.terminal || "—";

        const gateCell = createCell();
        const gateBadge = document.createElement("span");
        gateBadge.className = "gate-badge";
        gateBadge.textContent = flight.gate || "TBD";
        gateCell.append(gateBadge);

        const statusCell = createCell();
        const statusBadge = document.createElement("span");
        const safeStatus = flight.status
            .toLowerCase()
            .replace(/[^a-z_]/g, "");

        statusBadge.className = `flight-status flight-status--${safeStatus}`;

        if (flight.disruption_reason) {
            statusBadge.title = flight.disruption_reason;
        }

        const statusDot = document.createElement("span");
        statusDot.className = "flight-status__dot";

        const statusLabel = document.createElement("span");
        statusLabel.textContent = flight.status_label;

        statusBadge.append(statusDot, statusLabel);
        statusCell.append(statusBadge);

        row.append(
            timeCell,
            flightCell,
            airlineCell,
            routeCell,
            terminalCell,
            gateCell,
            statusCell,
        );

        return row;
    }

    function renderFlights(flights) {
        tableBody.replaceChildren();
        flights.forEach((flight) => tableBody.append(renderFlight(flight)));
        emptyState.hidden = flights.length > 0;
    }

    function updateBrowserUrl() {
        const url = new URL(window.location.href);
        url.searchParams.set("airport", airportSelect.value);
        url.searchParams.set("type", boardType);
        window.history.replaceState({}, "", url);
    }

    function setLoading(isLoading) {
        loading.hidden = !isLoading;
        refreshButton.disabled = isLoading;
        refreshButton.classList.toggle("refresh-button--loading", isLoading);
    }

    function showError(message) {
        errorBox.textContent = message;
        errorBox.hidden = false;
    }

    function hideError() {
        errorBox.hidden = true;
        errorBox.textContent = "";
    }

    async function loadFlights() {
        if (requestController) {
            requestController.abort();
        }

        requestController = new AbortController();
        setLoading(true);
        hideError();

        const query = new URLSearchParams({
            airport: airportSelect.value,
            type: boardType,
        });

        try {
            const response = await fetch(`${endpoint}?${query.toString()}`, {
                headers: { Accept: "application/json" },
                signal: requestController.signal,
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to load flight information.",
                );
            }

            airportHeading.textContent = data.airport.name;
            boardTypeLabel.textContent = boardType === "ARRIVALS"
                ? "Arrivals"
                : "Departures";
            routeHeading.textContent = boardType === "ARRIVALS"
                ? "Origin"
                : "Destination";
            lastUpdated.textContent = new Intl.DateTimeFormat("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
            }).format(new Date(data.updated_at));

            renderFlights(data.flights);
            updateBrowserUrl();
        } catch (error) {
            if (error.name !== "AbortError") {
                showError(error.message || "Live flight data is unavailable.");
            }
        } finally {
            if (requestController && !requestController.signal.aborted) {
                setLoading(false);
            }
        }
    }

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            boardType = tab.dataset.boardType;
            tabs.forEach((item) => {
                const isActive = item === tab;
                item.classList.toggle("board-tab--active", isActive);
                item.setAttribute("aria-selected", String(isActive));
            });
            loadFlights();
        });
    });

    airportSelect.addEventListener("change", loadFlights);
    refreshButton.addEventListener("click", loadFlights);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            loadFlights();
        }
    });

    const initialType = new URLSearchParams(window.location.search).get("type");
    if (initialType && ["ARRIVALS", "DEPARTURES"].includes(initialType.toUpperCase())) {
        boardType = initialType.toUpperCase();
        tabs.forEach((tab) => {
            const isActive = tab.dataset.boardType === boardType;
            tab.classList.toggle("board-tab--active", isActive);
            tab.setAttribute("aria-selected", String(isActive));
        });
    }

    updateClock();
    window.setInterval(updateClock, 1000);
    loadFlights();
    window.setInterval(() => {
        if (!document.hidden) {
            loadFlights();
        }
    }, 30000);
});
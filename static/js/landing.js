document.addEventListener(
    "DOMContentLoaded",
    () => {
        initializeCounters();
        initializePlatformTabs();
        initializeNavigation();
    }
);


function initializeCounters() {
    const counters = document.querySelectorAll(
        ".counter"
    );

    counters.forEach((counter) => {
        const target = Number(
            counter.dataset.target || 0
        );

        if (target <= 0) {
            counter.textContent = "0";
            return;
        }

        const duration = 650;

        const start = performance.now();

        const updateCounter = (time) => {
            const progress = Math.min(
                (time - start) / duration,
                1
            );

            const eased = (
                1 - Math.pow(
                    1 - progress,
                    3
                )
            );

            counter.textContent = (
                Math.round(
                    target * eased
                )
            );

            if (progress < 1) {
                requestAnimationFrame(
                    updateCounter
                );
            }
        };

        requestAnimationFrame(
            updateCounter
        );
    });
}


function initializePlatformTabs() {
    const tabs = document.querySelectorAll(
        ".platform-tab"
    );

    const panels = document.querySelectorAll(
        ".platform-panel"
    );

    tabs.forEach((tab) => {
        tab.addEventListener(
            "click",
            () => {
                const target = (
                    tab.dataset.tab
                );

                tabs.forEach((item) => {
                    item.classList.remove(
                        "active"
                    );
                });

                panels.forEach((panel) => {
                    panel.classList.remove(
                        "active"
                    );
                });

                tab.classList.add(
                    "active"
                );

                const targetPanel = (
                    document.getElementById(
                        target
                    )
                );

                if (targetPanel) {
                    targetPanel.classList.add(
                        "active"
                    );
                }
            }
        );
    });
}


function initializeNavigation() {
    const header = document.querySelector(
        ".landing-header"
    );

    const navLinks = document.querySelectorAll(
        '.main-navigation a[href^="#"]'
    );

    const sections = [
        "overview",
        "live",
        "platform",
        "engineering",
    ]
        .map((id) => (
            document.getElementById(id)
        ))
        .filter(Boolean);


    const updateHeader = () => {
        if (!header) {
            return;
        }

        header.classList.toggle(
            "scrolled",
            window.scrollY > 20
        );
    };


    window.addEventListener(
        "scroll",
        updateHeader,
        {
            passive: true,
        }
    );

    updateHeader();


    if (
        !("IntersectionObserver" in window)
    ) {
        return;
    }


    const observer = (
        new IntersectionObserver(
            (entries) => {
                entries.forEach(
                    (entry) => {
                        if (
                            !entry.isIntersecting
                        ) {
                            return;
                        }

                        const currentId = (
                            entry.target.id
                        );

                        navLinks.forEach(
                            (link) => {
                                const matches = (
                                    link.getAttribute(
                                        "href"
                                    )
                                    === `#${currentId}`
                                );

                                link.classList.toggle(
                                    "active",
                                    matches
                                );
                            }
                        );
                    }
                );
            },
            {
                rootMargin:
                    "-25% 0px -60% 0px",

                threshold: 0,
            }
        )
    );


    sections.forEach((section) => {
        observer.observe(section);
    });
}
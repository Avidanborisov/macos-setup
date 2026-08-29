// Karabiner (macos-setup) turns physical Ctrl+LeftShift / Ctrl+RightShift taps
// into F18 / F19 while Chrome is frontmost. Setting the dir attribute on the
// focused editable is the same base-direction change Chrome's own context menu
// (Writing Direction) performs.
(() => {
    const DIRS = { F18: "ltr", F19: "rtl" };

    function editableHost(el) {
        if (!el) return null;
        if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") return el;
        if (el.isContentEditable) {
            let host = el;
            while (host.parentElement && host.parentElement.isContentEditable) {
                host = host.parentElement;
            }
            return host;
        }
        return null;
    }

    addEventListener("keydown", (e) => {
        const dir = DIRS[e.code];
        if (!dir) return;
        const host = editableHost(document.activeElement);
        if (!host) return;
        e.preventDefault();
        e.stopPropagation();
        host.setAttribute("dir", dir);
    }, true);
})();

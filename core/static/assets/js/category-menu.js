document.addEventListener('DOMContentLoaded', function () {
    function collapseElement(el) {
        el.style.maxHeight = el.scrollHeight + 'px';
        // Force repaint
        el.offsetHeight; 
        el.style.maxHeight = '0px';
        el.classList.remove('show');
    }

    function expandElement(el) {
        el.style.maxHeight = el.scrollHeight + 'px';
        el.classList.add('show');
        // Remove inline style after transition to allow natural height
        setTimeout(function() { el.style.maxHeight = ''; }, 300);
    }

    function toggleSection(btn) {
        var wrapperId = btn.getAttribute('aria-controls');
        var wrapper = document.getElementById(wrapperId);
        if (!wrapper) return;

        var isOpen = wrapper.classList.contains('show');

        if (isOpen) {
            collapseElement(wrapper);
            btn.setAttribute('aria-expanded', 'false');
            btn.classList.remove('category-open');
        } else {
            expandElement(wrapper);
            btn.setAttribute('aria-expanded', 'true');
            btn.classList.add('category-open');
        }
    }

    document.body.addEventListener('click', function (e) {
        var btn = e.target.closest('.category-toggle');
        if (!btn) return;
        e.preventDefault();
        toggleSection(btn);
    });

    document.body.addEventListener('keydown', function (e) {
        var btn = e.target.closest && e.target.closest('.category-toggle');
        if (!btn) return;
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            btn.click();
        }
    });
});

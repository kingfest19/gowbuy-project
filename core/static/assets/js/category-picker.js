document.addEventListener('DOMContentLoaded', function () {
    function selectCategory(catId, catName) {
        var select = document.querySelector('select[name="category"]');
        var display = document.getElementById('selectedCategoryDisplay');
        if (select && catId) {
            select.value = catId;
            var ev = new Event('change', { bubbles: true });
            select.dispatchEvent(ev);
        }
        if (display) display.textContent = catName;
    }

    function updateBreadcrumb(container, crumbs) {
        var bc = container.querySelector('.picker-breadcrumb');
        if (!bc) return;
        bc.innerHTML = '';
        crumbs.forEach(function(crumb, idx) {
            if (idx) {
                var sep = document.createElement('span'); sep.className = 'crumb-sep'; sep.textContent = '›'; bc.appendChild(sep);
            }
            var a = document.createElement('a'); a.href = '#'; a.textContent = crumb.name; a.setAttribute('data-cat-id', crumb.id);
            a.addEventListener('click', function(e){ e.preventDefault(); navigateTo(crumb.id, container, crumbs.slice(0, idx+1)); });
            bc.appendChild(a);
        });
    }

    function navigateTo(catId, container, crumbs) {
        // Expand the node with id catId and collapse others for an inline focused view
        // Show breadcrumb
        updateBreadcrumb(container, crumbs || []);
        // Expand the corresponding subcategory wrapper for the catId if present
        var targetToggle = container.querySelector('[aria-controls$="picker-subcats-' + catId + '"]');
        if (targetToggle) {
            // Simulate click to expand it (uses category-menu behaviour)
            targetToggle.click();
        }
    }

    function initPicker(container) {
        if (!container) return;
        var crumbs = [];
        // Add breadcrumb container at top
        var bc = document.createElement('div'); bc.className = 'picker-breadcrumb mb-2';
        container.insertBefore(bc, container.firstChild);

        // Handle clicks on picker-select (leaf selections)
        container.addEventListener('click', function(e){
            var leaf = e.target.closest && e.target.closest('.picker-select');
            if (leaf) {
                e.preventDefault();
                selectCategory(leaf.getAttribute('data-category-id'), leaf.getAttribute('data-category-name'));
                // If container is inside a modal, close the modal
                var modal = container.closest('.modal');
                if (modal && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    var bm = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
                    bm.hide();
                }
            }
        });

        // Clicking a picker label should navigate into that label's children and update breadcrumb
        container.addEventListener('click', function(e){
            var label = e.target.closest && e.target.closest('.picker-label');
            if (!label) return;
            e.preventDefault();
            var node = label.closest('.category-item');
            if (!node) return;
            var id = label.getAttribute('data-category-id');
            var name = label.getAttribute('data-category-name');
            crumbs.push({id: id, name: name});
            updateBreadcrumb(container, crumbs);
            // Optionally collapse siblings and expand children for focused navigation
            var targetWrapper = container.querySelector('[id$="picker-subcats-' + id + '"]');
            if (targetWrapper && !targetWrapper.classList.contains('show')) {
                var toggleBtn = container.querySelector('[aria-controls$="picker-subcats-' + id + '"]');
                if (toggleBtn) toggleBtn.click();
            }
        });

        // Allow breadcrumb click to go back (handled by updateBreadcrumb navigation)
    }

    // Initialize modal picker and inline picker if present
    var modal = document.getElementById('categoryPickerModal');
    if (modal) initPicker(modal.querySelector('.modal-body'));
    var inlinePicker = document.getElementById('categoryInlinePicker');
    if (inlinePicker) initPicker(inlinePicker);
});

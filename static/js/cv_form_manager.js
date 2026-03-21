/**
 * CV Form Manager - Dynamic form field management for CV data editing
 * Provides reusable functions for adding/removing form fields dynamically
 */

const CVFormManager = {
    /**
     * Add a new item to a container with a template
     * @param {string} containerId - ID of the container element
     * @param {string} templateId - ID of the template element
     * @param {string} itemClass - Class name for the item wrapper
     */
    addItem: function (containerId, templateId, itemClass) {
        const container = document.getElementById(containerId);
        const template = document.getElementById(templateId);

        if (!container || !template) {
            console.error('Container or template not found');
            return;
        }

        // Clone the template
        const clone = template.content.cloneNode(true);

        // Update indices in the cloned content
        const items = container.querySelectorAll(`.${itemClass}`);
        const newIndex = items.length;

        // Replace all index placeholders with the new index
        const wrapper = document.createElement('div');
        wrapper.appendChild(clone);
        let html = wrapper.innerHTML;
        html = html.replace(/\{INDEX\}/g, newIndex);
        wrapper.innerHTML = html;

        // Append to container
        container.appendChild(wrapper.firstElementChild);

        // Scroll to the new item
        const newItem = container.lastElementChild;
        newItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    /**
     * Remove an item from the form
     * @param {HTMLElement} button - The remove button that was clicked
     * @param {string} itemClass - Class name of the item to remove
     */
    removeItem: function (button, itemClass) {
        const item = button.closest(`.${itemClass}`);
        if (!item) {
            console.error('Item not found');
            return;
        }

        const container = item.parentElement;
        const items = container.querySelectorAll(`.${itemClass}`);

        // Don't allow removing the last item
        if (items.length <= 1) {
            alert('You must have at least one item.');
            return;
        }

        // Confirm deletion
        if (confirm('Are you sure you want to remove this item?')) {
            item.remove();
            // Re-index remaining items
            this.reindexItems(container, itemClass);
        }
    },

    /**
     * Re-index all items in a container after removal
     * @param {HTMLElement} container - The container element
     * @param {string} itemClass - Class name of items to re-index
     */
    reindexItems: function (container, itemClass) {
        const items = container.querySelectorAll(`.${itemClass}`);
        items.forEach((item, index) => {
            // Update all name attributes
            const inputs = item.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.name) {
                    // Replace the index in the name attribute
                    input.name = input.name.replace(/\[\d+\]/, `[${index}]`);
                }
                if (input.id) {
                    // Replace the index in the id attribute
                    input.id = input.id.replace(/_\d+_/, `_${index}_`);
                }
            });

            // Update labels
            const labels = item.querySelectorAll('label');
            labels.forEach(label => {
                if (label.htmlFor) {
                    label.htmlFor = label.htmlFor.replace(/_\d+_/, `_${index}_`);
                }
            });
        });
    },

    /**
     * Add a nested item (e.g., achievement within experience)
     * @param {HTMLElement} button - The add button that was clicked
     * @param {string} templateId - ID of the template element
     * @param {string} containerClass - Class name of the container
     * @param {string} itemClass - Class name for the nested item
     */
    addNestedItem: function (button, templateId, containerClass, itemClass) {
        const container = button.closest('.experience-item, .project-item')
            .querySelector(`.${containerClass}`);
        const template = document.getElementById(templateId);

        if (!container || !template) {
            console.error('Container or template not found');
            return;
        }

        // Get parent index
        const parentItem = button.closest('.experience-item, .project-item');
        const parentIndex = Array.from(parentItem.parentElement.children).indexOf(parentItem);

        // Get nested item count
        const nestedItems = container.querySelectorAll(`.${itemClass}`);
        const nestedIndex = nestedItems.length;

        // Clone template
        const clone = template.content.cloneNode(true);
        const wrapper = document.createElement('div');
        wrapper.appendChild(clone);

        // Replace placeholders
        let html = wrapper.innerHTML;
        html = html.replace(/\{PARENT_INDEX\}/g, parentIndex);
        html = html.replace(/\{NESTED_INDEX\}/g, nestedIndex);
        wrapper.innerHTML = html;

        // Append to container
        container.appendChild(wrapper.firstElementChild);

        // Scroll to new item
        const newItem = container.lastElementChild;
        newItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    /**
     * Remove a nested item
     * @param {HTMLElement} button - The remove button that was clicked
     * @param {string} itemClass - Class name of the nested item
     */
    removeNestedItem: function (button, itemClass) {
        const item = button.closest(`.${itemClass}`);
        if (!item) {
            console.error('Item not found');
            return;
        }

        const container = item.parentElement;
        const items = container.querySelectorAll(`.${itemClass}`);

        // Don't allow removing the last item
        if (items.length <= 1) {
            alert('You must have at least one item.');
            return;
        }

        // Confirm deletion
        if (confirm('Are you sure you want to remove this item?')) {
            item.remove();
            // Re-index remaining nested items
            this.reindexNestedItems(container, itemClass);
        }
    },

    /**
     * Re-index nested items after removal
     * @param {HTMLElement} container - The container element
     * @param {string} itemClass - Class name of nested items
     */
    reindexNestedItems: function (container, itemClass) {
        const parentItem = container.closest('.experience-item, .project-item');
        const parentIndex = Array.from(parentItem.parentElement.children).indexOf(parentItem);
        const items = container.querySelectorAll(`.${itemClass}`);

        items.forEach((item, index) => {
            const inputs = item.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.name) {
                    // Update nested index in name
                    const namePattern = new RegExp(`\\[${parentIndex}\\]\\[\\w+\\]\\[\\d+\\]`);
                    input.name = input.name.replace(namePattern, `[${parentIndex}][achievements][${index}]`);
                }
                if (input.id) {
                    // Update nested index in id
                    input.id = input.id.replace(/_\d+_achievement_\d+_/, `_${parentIndex}_achievement_${index}_`);
                }
            });

            const labels = item.querySelectorAll('label');
            labels.forEach(label => {
                if (label.htmlFor) {
                    label.htmlFor = label.htmlFor.replace(/_\d+_achievement_\d+_/, `_${parentIndex}_achievement_${index}_`);
                }
            });
        });
    },

    /**
     * Initialize form validation
     */
    initValidation: function () {
        const forms = document.querySelectorAll('form[data-validate="true"]');
        forms.forEach(form => {
            form.addEventListener('submit', function (e) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    },

    /**
     * Add a simple text field (for soft skills, keywords, etc.)
     * @param {HTMLElement} button - The add button
     * @param {string} containerClass - Class of the container
     * @param {string} fieldName - Name attribute for the input
     * @param {string} placeholder - Placeholder text
     */
    addTextField: function (button, containerClass, fieldName, placeholder) {
        const container = button.previousElementSibling;
        if (!container || !container.classList.contains(containerClass)) {
            console.error('Container not found');
            return;
        }

        const index = container.children.length;
        const div = document.createElement('div');
        div.className = 'input-group mb-2';
        div.innerHTML = `
            <input type="text" class="form-control" name="${fieldName}[${index}]" 
                   placeholder="${placeholder}" required>
            <button type="button" class="btn btn-outline-danger" 
                    onclick="this.parentElement.remove()">
                <i class="bi bi-trash"></i>
            </button>
        `;
        container.appendChild(div);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    CVFormManager.initValidation();
});


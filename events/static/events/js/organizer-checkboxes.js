document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('select.js-organizer-select').forEach(function (select) {
        var container = document.querySelector('[data-organizer-checkboxes-for="' + select.id + '"]');
        if (!container) return;

        container.querySelectorAll('input[type="checkbox"]').forEach(function (checkbox) {
            var option = select.querySelector('option[value="' + checkbox.value + '"]');
            if (!option) return;

            checkbox.checked = option.selected;
            checkbox.addEventListener('change', function () {
                option.selected = checkbox.checked;
            });
        });
    });
});

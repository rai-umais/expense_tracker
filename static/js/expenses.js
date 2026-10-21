// Kharcha Tracker Client-Side Helpers

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss success flash alerts after 5 seconds
    const successFlashes = document.querySelectorAll('.flash-success');
    successFlashes.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.4s ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                alert.remove();
            }, 400);
        }, 5000);
    });

    // Close modals on Escape key press
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal-overlay');
            modals.forEach(function (modal) {
                modal.style.display = 'none';
            });
        }
    });
});

// Confirm JS is loaded

console.log("Belleful Express loaded successfully");

// Auto-hide Django messages

document.addEventListener("DOMContentLoaded", function () {

    const alerts = document.querySelectorAll(
        ".alert-success, .alert-error"
    );

    alerts.forEach(function(alert) {

        setTimeout(function() {

            alert.style.transition = "0.5s";
            alert.style.opacity = "0";

            setTimeout(function() {
                alert.remove();
            }, 500);

        }, 4000);

    });

});
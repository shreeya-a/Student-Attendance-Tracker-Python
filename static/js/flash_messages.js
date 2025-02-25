document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        let flashMessages = document.getElementById("flash-messages");
        if (flashMessages) {
            flashMessages.style.transition = "opacity 0.5s";
            flashMessages.style.opacity = "0";
            setTimeout(() => flashMessages.remove(), 500); // Remove after fade-out
        }
    }, 2000);
});

// myapp/static/myapp/js/my_custom_admin.js
document.addEventListener('DOMContentLoaded', function() {
    // Target a specific input field by its ID
    const myFieldInput = document.getElementById('id_name'); 
    if (myFieldInput) {
        myFieldInput.setAttribute('readonly', 'readonly');
        // Optionally, add a class for styling
        myFieldInput.classList.add('readonly-field'); 
    }

    // Example for a RichTextField (often requires more complex handling)
    // You might need to interact with the underlying editor instance (e.g., TinyMCE, Draftail)
    // to truly disable it, rather than just the textarea.
    // This is more advanced and depends on the specific editor.
});

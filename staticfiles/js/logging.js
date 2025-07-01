const avatarDropdown = document.getElementById('avatarDropdown');
const userDropdown = document.getElementById('userDropdown');

avatarDropdown.addEventListener('click', (e) => {
    e.stopPropagation();
    avatarDropdown.classList.toggle('active');
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!avatarDropdown.contains(e.target)) {
        avatarDropdown.classList.remove('active');
    }
});

// Prevent form submission from closing dropdown
userDropdown.addEventListener('click', (e) => {
    e.stopPropagation();
});

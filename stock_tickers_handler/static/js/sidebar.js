function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    var mainContent = document.getElementById("main-content");
    var items = document.querySelectorAll('.sidebar-item');

    if (sidebar.style.width === "250px") {
        sidebar.style.width = "60px"; // Zmniejszenie do szerokości ikon
        mainContent.style.marginLeft = "60px"; // Ustawienie marginesu dla głównej zawartości
        items.forEach(item => {
            item.innerHTML = `<i class="${item.firstElementChild.className}"></i>`; // Utrzymanie tylko ikony
        });
    } else {
        sidebar.style.width = "250px"; // Powiększenie do pełnej szerokości
        mainContent.style.marginLeft = "250px"; // Ustawienie marginesu dla głównej zawartości
        items.forEach(item => {
            item.innerHTML = `<i class="${item.firstElementChild.className}"></i> ${item.dataset.title}`; // Dodanie tytułu z powrotem
        });
    }
}

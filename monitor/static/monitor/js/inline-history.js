waitForElementToExist('#id_member_problems-ADD').then(element => {
    console.log('The element exists', element);
    const elements = document.querySelectorAll('[id$="-DELETE-button"]');
    elements.forEach(e => {
        e.style.display = "none";
        console.log(e);
    });
    element.style.display = "none";
});


waitForElementToExist('#id_member_problems-ADD').then(element => {
    console.log('The element exists', element);
    const elements = document.querySelectorAll('[id$="-DELETE-button"]');
    elements.forEach(e => {
        e.style.display = "none";
        console.log(e);
    });
    /* Disable edit textarea */
    const elements_textarea = document.querySelectorAll('[id$="-update_progress"]');
    elements_textarea.forEach(e => {
        e.readOnly = "false";
    });
    /*
    console.log(elements_textarea);
    */
});


/*
setTimeout(() => {

    const elements = document.querySelectorAll('[id$="-DELETE-button"]');
    //let elements = document.querySelectorAll('[title="Delete"]');
    elements.forEach(e => {
        e.style.display = "none";
        console.log(e);
    });

}, 1000);
*/
